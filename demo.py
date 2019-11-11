bb = BenchBot('ADDRESS')

agent = MyAgent(bb.actions)

observation = bb.reset()
while not agent.is_done():
    action = agent.policy_function(observation)
    observation, reward, info = env.step(action)

bb.finish(agent.get_result())
