import asyncio
import unittest
from turncraft import Agent, DemoTools, Event, replay

class AgentTests(unittest.IsolatedAsyncioTestCase):
    async def test_interrupt_cancels_output(self):
        agent = Agent(speech_delay=1)
        await agent.handle(Event('transcript', text='hello'))
        await agent.handle(Event('speech_start'))
        self.assertEqual(agent.state, 'listening')
        self.assertEqual(agent.output, [])
        self.assertIn('speech_cancelled', [x['action'] for x in agent.trace])

    async def test_booking_requires_confirmation(self):
        agent = Agent(speech_delay=0)
        await agent.handle(Event('transcript', text='book me please'))
        await agent.flush()
        self.assertEqual(len(agent.tools.slots), 2)

    async def test_idempotent_booking(self):
        tools = DemoTools()
        a = await tools.book(tools.slots[0], 'a')
        self.assertEqual(await tools.book('2030-01-10T10:00:00Z', 'a'), a)
        self.assertEqual(len(tools.slots), 1)
        with self.assertRaises(ValueError):
            await tools.book(tools.slots[0], 'a')

    async def test_concurrent_conflict(self):
        tools = DemoTools()
        slot = tools.slots[0]
        results = await asyncio.gather(tools.book(slot, 'a'), tools.book(slot, 'b'), return_exceptions=True)
        self.assertEqual(sum(isinstance(x, ValueError) for x in results), 1)

    async def test_timeout(self):
        class Slow(DemoTools):
            async def availability(self, day):
                await asyncio.sleep(1)
        agent = Agent(Slow(), timeout=.001, speech_delay=0)
        await agent.handle(Event('transcript', text='available'))
        await agent.flush()
        self.assertIn('tool_failed', [x['action'] for x in agent.trace])

    async def test_handoff(self):
        trace = await replay([{'kind':'transcript', 'text':'human please'}])
        self.assertIn('handoff_requested', [x['action'] for x in trace])

    async def test_closed_rejects_events(self):
        agent = Agent()
        await agent.handle(Event('hangup'))
        with self.assertRaises(ValueError):
            await agent.handle(Event('speech_start'))

    async def test_unknown_event(self):
        with self.assertRaises(ValueError):
            await Agent().handle(Event('nonsense'))

    async def test_missing_booking_data(self):
        agent = Agent(speech_delay=0)
        await agent.handle(Event('confirm_booking'))
        await agent.flush()
        self.assertIn('tool_failed', [x['action'] for x in agent.trace])
