const { AccessToken, AgentDispatchClient } = require('livekit-server-sdk');

module.exports = async function handler(req, res) {
  // CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  if (req.method === 'OPTIONS') return res.status(200).end();

  const apiKey    = process.env.LIVEKIT_API_KEY;
  const apiSecret = process.env.LIVEKIT_API_SECRET;
  const lkUrl     = process.env.LIVEKIT_URL;

  if (!apiKey || !apiSecret || !lkUrl) {
    return res.status(500).json({ error: 'Server configuration missing. Check Vercel environment variables.' });
  }

  // ── Customize: room name ──
  const roomName = 'demo-room';

  const identity = 'user-' + Date.now();

  // 1. Token generate karo
  const at = new AccessToken(apiKey, apiSecret, {
    identity,
    name: 'User',
    ttl: '1h',
  });
  at.addGrant({ roomJoin: true, room: roomName, canPublish: true, canSubscribe: true });
  const token = await at.toJwt();

  // 2. Agent ko room mein dispatch karo
  // agent_name 'my-agent' = hamara custom agent (matches @server.rtc_session(agent_name="my-agent"))
  try {
    const dispatch = new AgentDispatchClient(lkUrl, apiKey, apiSecret);
    await dispatch.createDispatch(roomName, 'my-agent');
    console.log('✓ Agent dispatched to room:', roomName, 'with agent_name: my-agent');
  } catch (err) {
    console.warn('✗ Agent dispatch failed:', err.message);
  }

  return res.status(200).json({ url: lkUrl, token });
};
