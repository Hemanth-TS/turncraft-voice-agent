"""Offline voice-workflow model. Not an STT, LLM, TTS or LiveKit client."""
import argparse
import asyncio
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Protocol

class Tools(Protocol):
    async def availability(self, day: str) -> list[str]: ...
    async def book(self, slot: str, request_id: str) -> str: ...

class DemoTools:
    """Single-process fictional calendar; request IDs make retries idempotent."""
    def __init__(self):
        self.slots = ['2030-01-10T10:00:00Z', '2030-01-10T14:00:00Z']
        self.receipts = {}
        self.lock = asyncio.Lock()

    async def availability(self, day):
        return [slot for slot in self.slots if slot.startswith(day)]

    async def book(self, slot, request_id):
        async with self.lock:
            if request_id in self.receipts:
                old_slot, receipt = self.receipts[request_id]
                if old_slot != slot:
                    raise ValueError('request_id reused for a different slot')
                return receipt
            if slot not in self.slots:
                raise ValueError('slot unavailable')
            self.slots.remove(slot)
            receipt = f'demo-{len(self.receipts)+1:03d}'
            self.receipts[request_id] = (slot, receipt)
            return receipt

@dataclass(frozen=True)
class Event:
    kind: str
    text: str = ''
    slot: str = ''
    request_id: str = ''

class Agent:
    """Serialized event reducer; outbound speech is a cancellable async task."""
    def __init__(self, tools=None, timeout=1.0, speech_delay=0.01):
        if timeout <= 0 or speech_delay < 0:
            raise ValueError('invalid timing configuration')
        self.tools = tools or DemoTools()
        self.timeout, self.speech_delay = timeout, speech_delay
        self.state = 'listening'
        self.trace = []
        self.output = []
        self.speech = None
        self.lock = asyncio.Lock()

    def record(self, action, **fields):
        self.trace.append(dict(seq=len(self.trace), state=self.state, action=action, **fields))

    async def stop_speech(self):
        if self.speech and not self.speech.done():
            self.speech.cancel()
            try:
                await self.speech
            except asyncio.CancelledError:
                pass
            self.record('speech_cancelled')

    async def say(self, text):
        self.state = 'speaking'
        self.record('speech_started', text=text)
        async def emit():
            for token in text.split():
                await asyncio.sleep(self.speech_delay)
                self.output.append(token)
            self.state = 'listening'
            self.record('speech_finished')
        self.speech = asyncio.create_task(emit())

    async def handle(self, event):
        async with self.lock:
            if self.state == 'closed':
                raise ValueError('session closed')
            if event.kind not in {'speech_start', 'transcript', 'confirm_booking', 'hangup'}:
                raise ValueError('unknown event kind')
            await self.stop_speech()
            if event.kind == 'hangup':
                self.state = 'closed'
                self.record('session_closed')
                return
            self.state = 'listening'
            if event.kind == 'speech_start':
                self.record('user_started')
                return
            self.record('input_received', kind=event.kind)
            try:
                if event.kind == 'confirm_booking':
                    if not event.slot or not event.request_id:
                        raise ValueError('explicit slot and request_id required')
                    self.state = 'tool_pending'
                    receipt = await asyncio.wait_for(self.tools.book(event.slot, event.request_id), self.timeout)
                    self.record('booking_confirmed', receipt=receipt)
                    await self.say(f'Your demo booking is confirmed: {receipt}.')
                elif 'available' in event.text.lower():
                    self.state = 'tool_pending'
                    slots = await asyncio.wait_for(self.tools.availability('2030-01-10'), self.timeout)
                    self.record('availability_returned', count=len(slots))
                    await self.say('Available demo slots: '+', '.join(slots))
                elif any(w in event.text.lower() for w in ('human', 'emergency')):
                    self.record('handoff_requested')
                    await self.say('Please contact a human. This demo cannot place calls or provide medical advice.')
                else:
                    await self.say('I can list demo availability. Booking requires a separate confirmation event.')
            except (asyncio.TimeoutError, ValueError) as error:
                self.record('tool_failed', reason=type(error).__name__)
                await self.say('I could not complete that request. Please ask a human to help.')

    async def flush(self):
        if self.speech:
            await self.speech

async def replay(events):
    agent = Agent()
    for row in events:
        event = Event(**row)
        await agent.handle(event)
        if event.kind != 'hangup':
            await agent.flush()
    return agent.trace

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scenario', type=Path, default=Path(__file__).parent/'samples/scenario.json')
    args = parser.parse_args()
    print(json.dumps(asyncio.run(replay(json.loads(args.scenario.read_text()))), indent=2))

if __name__ == '__main__':
    main()
