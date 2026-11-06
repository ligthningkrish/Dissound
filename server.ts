import express, { Request, Response } from 'express';
import cors from 'cors';
import path from 'path';
import fs from 'fs';
import { createServer as createViteServer } from 'vite';

const app = express();
const PORT = 3000;
const HOST = '0.0.0.0';

app.use(cors());
app.use(express.json());

// In-memory data store replicating Dissound SQLite repository
interface SoundItem {
  sound_id: string;
  sound_name: string;
  category: string;
  file_path: string;
  duration: number;
  file_size: number;
  file_format: string;
  source_url: string;
  tags: string;
  created_at: string;
  emoji?: string;
  play_count?: number;
}

interface SoundboardSound {
  id: string;
  name: string;
  sound_id: string;
  volume: number;
  emoji?: string;
  user: {
    id: string;
    username: string;
    avatar?: string;
  };
  added_at: string;
  file_path: string;
  duration: number;
}

interface ServerData {
  id: string;
  name: string;
  icon: string;
  premium_tier: number; // 0, 1, 2, 3
  premium_subscription_count: number;
  sound_limit: number;
  sounds: SoundboardSound[];
}

interface UploadHistoryItem {
  upload_id: number;
  server_id: string;
  server_name: string;
  user_id: string;
  username: string;
  sound_id: string;
  sound_name: string;
  upload_status: 'SUCCESS' | 'FAILED';
  error_message: string | null;
  timestamp: string;
}

const TIER_SOUNDBOARD_SLOTS: Record<number, number> = {
  0: 8,
  1: 24,
  2: 36,
  3: 48,
};

// Initial meme catalog matching bundled assets
let soundCatalog: SoundItem[] = [
  {
    sound_id: 'vine_boom',
    sound_name: 'Vine Boom',
    category: 'Meme Sounds',
    file_path: '/sounds/vine_boom.mp3',
    duration: 1.5,
    file_size: 25120,
    file_format: 'mp3',
    source_url: 'Iconic Vine Sound Effect',
    tags: 'vine, boom, bass, thud, dramatic, sound effect',
    created_at: new Date(Date.now() - 86400000 * 5).toISOString(),
    emoji: '💥',
    play_count: 342,
  },
  {
    sound_id: 'metal_pipe',
    sound_name: 'Metal Pipe',
    category: 'Random & Funny',
    file_path: '/sounds/metal_pipe.mp3',
    duration: 1.8,
    file_size: 29718,
    file_format: 'mp3',
    source_url: 'Falling Metal Pipe Meme',
    tags: 'metal, pipe, falling, clang, loud, funny',
    created_at: new Date(Date.now() - 86400000 * 4).toISOString(),
    emoji: '🔩',
    play_count: 289,
  },
  {
    sound_id: 'windows_error',
    sound_name: 'Windows XP Error',
    category: 'Classic Internet',
    file_path: '/sounds/windows_error.mp3',
    duration: 1.2,
    file_size: 20105,
    file_format: 'mp3',
    source_url: 'Microsoft Windows XP OS Sound',
    tags: 'windows, xp, error, alert, classic, microsoft',
    created_at: new Date(Date.now() - 86400000 * 6).toISOString(),
    emoji: '💻',
    play_count: 195,
  },
  {
    sound_id: 'airhorn',
    sound_name: 'Airhorn',
    category: 'Random & Funny',
    file_path: '/sounds/airhorn.mp3',
    duration: 1.2,
    file_size: 20105,
    file_format: 'mp3',
    source_url: 'MLG 360 Triple Airhorn',
    tags: 'airhorn, mlg, hype, horn, celebration, montage',
    created_at: new Date(Date.now() - 86400000 * 7).toISOString(),
    emoji: '📢',
    play_count: 245,
  },
  {
    sound_id: 'roblox_oof',
    sound_name: 'Roblox Oof',
    category: 'Gaming',
    file_path: '/sounds/roblox_oof.mp3',
    duration: 0.9,
    file_size: 15507,
    file_format: 'mp3',
    source_url: 'Classic Roblox Death Sound',
    tags: 'roblox, oof, death, gaming, funny, messiah',
    created_at: new Date(Date.now() - 86400000 * 8).toISOString(),
    emoji: '🧱',
    play_count: 310,
  },
  {
    sound_id: 'bruh',
    sound_name: 'Bruh Sound Effect',
    category: 'Meme Sounds',
    file_path: '/sounds/bruh.mp3',
    duration: 1.2,
    file_size: 20105,
    file_format: 'mp3',
    source_url: 'Bruh #2 Sound Effect',
    tags: 'bruh, meme, reaction, disappointment, funny',
    created_at: new Date(Date.now() - 86400000 * 9).toISOString(),
    emoji: '🗿',
    play_count: 278,
  },
  {
    sound_id: 'bonk',
    sound_name: 'Bonk',
    category: 'Reactions',
    file_path: '/sounds/bonk.mp3',
    duration: 0.8,
    file_size: 13835,
    file_format: 'mp3',
    source_url: 'Cheems Mallet Bonk',
    tags: 'bonk, hammer, cartoon, doge, horny jail, bat',
    created_at: new Date(Date.now() - 86400000 * 3).toISOString(),
    emoji: '🔨',
    play_count: 260,
  },
  {
    sound_id: 'among_us',
    sound_name: 'Among Us Impostor',
    category: 'Gaming',
    file_path: '/sounds/among_us.mp3',
    duration: 1.4,
    file_size: 23448,
    file_format: 'mp3',
    source_url: 'Innersloth Among Us Kill Chime',
    tags: 'among us, sus, impostor, kill, gaming, red',
    created_at: new Date(Date.now() - 86400000 * 2).toISOString(),
    emoji: '🔪',
    play_count: 320,
  },
  {
    sound_id: 'anime_wow',
    sound_name: 'Anime Wow',
    category: 'Reactions',
    file_path: '/sounds/anime_wow.mp3',
    duration: 1.0,
    file_size: 17179,
    file_format: 'mp3',
    source_url: 'Fairy Tail Anime Wow Effect',
    tags: 'anime, wow, cute, reaction, fairy, sparkle',
    created_at: new Date(Date.now() - 86400000 * 1).toISOString(),
    emoji: '✨',
    play_count: 180,
  },
  {
    sound_id: 'tada',
    sound_name: 'Tada Fanfare',
    category: 'Reactions',
    file_path: '/sounds/tada.mp3',
    duration: 1.5,
    file_size: 25120,
    file_format: 'mp3',
    source_url: 'Fanfare Brass Resolution',
    tags: 'tada, success, fanfare, winner, cheer, celebration',
    created_at: new Date().toISOString(),
    emoji: '🎉',
    play_count: 145,
  },
];

// Mock Discord Servers with soundboards
let servers: Record<string, ServerData> = {
  'guild_101': {
    id: 'guild_101',
    name: 'Meme Haven 🎮',
    icon: '⚡',
    premium_tier: 1, // 24 slots
    premium_subscription_count: 3,
    sound_limit: 24,
    sounds: [
      {
        id: 'sb_1',
        name: 'vine boom',
        sound_id: 'vine_boom',
        volume: 0.9,
        emoji: '💥',
        user: { id: 'u_1', username: 'KaranJ' },
        added_at: new Date(Date.now() - 3600000 * 12).toISOString(),
        file_path: '/sounds/vine_boom.mp3',
        duration: 1.5,
      },
      {
        id: 'sb_2',
        name: 'metal pipe',
        sound_id: 'metal_pipe',
        volume: 0.8,
        emoji: '🔩',
        user: { id: 'u_2', username: 'AlexW' },
        added_at: new Date(Date.now() - 3600000 * 8).toISOString(),
        file_path: '/sounds/metal_pipe.mp3',
        duration: 1.8,
      },
      {
        id: 'sb_3',
        name: 'airhorn',
        sound_id: 'airhorn',
        volume: 1.0,
        emoji: '📢',
        user: { id: 'u_3', username: 'SamG' },
        added_at: new Date(Date.now() - 3600000 * 4).toISOString(),
        file_path: '/sounds/airhorn.mp3',
        duration: 1.2,
      },
      {
        id: 'sb_4',
        name: 'roblox oof',
        sound_id: 'roblox_oof',
        volume: 0.85,
        emoji: '🧱',
        user: { id: 'u_1', username: 'KaranJ' },
        added_at: new Date(Date.now() - 3600000 * 2).toISOString(),
        file_path: '/sounds/roblox_oof.mp3',
        duration: 0.9,
      },
    ],
  },
  'guild_102': {
    id: 'guild_102',
    name: 'Voice Chat Chill',
    icon: '☕',
    premium_tier: 0, // 8 slots
    premium_subscription_count: 0,
    sound_limit: 8,
    sounds: [
      {
        id: 'sb_21',
        name: 'bonk',
        sound_id: 'bonk',
        volume: 0.8,
        emoji: '🔨',
        user: { id: 'u_4', username: 'Emily' },
        added_at: new Date(Date.now() - 3600000 * 24).toISOString(),
        file_path: '/sounds/bonk.mp3',
        duration: 0.8,
      },
      {
        id: 'sb_22',
        name: 'bruh',
        sound_id: 'bruh',
        volume: 0.9,
        emoji: '🗿',
        user: { id: 'u_5', username: 'Liam' },
        added_at: new Date(Date.now() - 3600000 * 18).toISOString(),
        file_path: '/sounds/bruh.mp3',
        duration: 1.2,
      },
    ],
  },
  'guild_103': {
    id: 'guild_103',
    name: 'Esports Arena (Full Slots)',
    icon: '🏆',
    premium_tier: 0, // 8 slots max, filled to 8 to test capacity warning
    premium_subscription_count: 0,
    sound_limit: 8,
    sounds: [
      { id: 'sb_31', name: 'vine boom', sound_id: 'vine_boom', volume: 1.0, emoji: '💥', user: { id: 'u_6', username: 'ProGamer' }, added_at: new Date().toISOString(), file_path: '/sounds/vine_boom.mp3', duration: 1.5 },
      { id: 'sb_32', name: 'airhorn', sound_id: 'airhorn', volume: 1.0, emoji: '📢', user: { id: 'u_6', username: 'ProGamer' }, added_at: new Date().toISOString(), file_path: '/sounds/airhorn.mp3', duration: 1.2 },
      { id: 'sb_33', name: 'bonk', sound_id: 'bonk', volume: 0.9, emoji: '🔨', user: { id: 'u_7', username: 'Viper' }, added_at: new Date().toISOString(), file_path: '/sounds/bonk.mp3', duration: 0.8 },
      { id: 'sb_34', name: 'among us', sound_id: 'among_us', volume: 0.8, emoji: '🔪', user: { id: 'u_8', username: 'Ghost' }, added_at: new Date().toISOString(), file_path: '/sounds/among_us.mp3', duration: 1.4 },
      { id: 'sb_35', name: 'metal pipe', sound_id: 'metal_pipe', volume: 0.7, emoji: '🔩', user: { id: 'u_6', username: 'ProGamer' }, added_at: new Date().toISOString(), file_path: '/sounds/metal_pipe.mp3', duration: 1.8 },
      { id: 'sb_36', name: 'windows error', sound_id: 'windows_error', volume: 0.9, emoji: '💻', user: { id: 'u_9', username: 'Kernel' }, added_at: new Date().toISOString(), file_path: '/sounds/windows_error.mp3', duration: 1.2 },
      { id: 'sb_37', name: 'anime wow', sound_id: 'anime_wow', volume: 0.85, emoji: '✨', user: { id: 'u_7', username: 'Viper' }, added_at: new Date().toISOString(), file_path: '/sounds/anime_wow.mp3', duration: 1.0 },
      { id: 'sb_38', name: 'tada fanfare', sound_id: 'tada', volume: 1.0, emoji: '🎉', user: { id: 'u_8', username: 'Ghost' }, added_at: new Date().toISOString(), file_path: '/sounds/tada.mp3', duration: 1.5 },
    ],
  },
};

// Upload history log
let uploadHistory: UploadHistoryItem[] = [
  {
    upload_id: 1,
    server_id: 'guild_101',
    server_name: 'Meme Haven 🎮',
    user_id: 'u_1',
    username: 'KaranJ',
    sound_id: 'vine_boom',
    sound_name: 'vine boom',
    upload_status: 'SUCCESS',
    error_message: null,
    timestamp: new Date(Date.now() - 3600000 * 12).toISOString(),
  },
  {
    upload_id: 2,
    server_id: 'guild_101',
    server_name: 'Meme Haven 🎮',
    user_id: 'u_2',
    username: 'AlexW',
    sound_id: 'metal_pipe',
    sound_name: 'metal pipe',
    upload_status: 'SUCCESS',
    error_message: null,
    timestamp: new Date(Date.now() - 3600000 * 8).toISOString(),
  },
  {
    upload_id: 3,
    server_id: 'guild_103',
    server_name: 'Esports Arena (Full Slots)',
    user_id: 'u_6',
    username: 'ProGamer',
    sound_id: 'bruh',
    sound_name: 'bruh sound',
    upload_status: 'FAILED',
    error_message: 'Soundboard capacity reached (8/8 slots used). Upgrade server boost tier for more slots.',
    timestamp: new Date(Date.now() - 3600000 * 1).toISOString(),
  },
];

// Serve static sounds from public/sounds
app.use('/sounds', express.static(path.resolve('public/sounds')));

// --- REST API Endpoints ---

// 1. Health check & Bot Info
app.get('/api/bot/info', (req: Request, res: Response) => {
  res.json({
    status: 'online',
    name: 'Dissound (MemeSound Bot)',
    version: '2.5.0',
    discord_py: '2.5.0+',
    total_sounds: soundCatalog.length,
    active_servers: Object.keys(servers).length,
    bot_permissions: [
      'Create Expressions (CREATE_GUILD_EXPRESSIONS)',
      'Manage Expressions (MANAGE_GUILD_EXPRESSIONS)',
      'Send Messages',
      'Embed Links',
      'Attach Files',
      'Read Message History',
    ],
    supported_audio_specs: {
      max_duration_sec: 5.2,
      max_file_size_kb: 512,
      supported_formats: ['mp3', 'ogg'],
      sound_name_length: '2-32 characters',
      volume_range: '0.1 - 1.0',
    },
    tier_limits: TIER_SOUNDBOARD_SLOTS,
  });
});

// 2. Sounds catalog & search
app.get('/api/sounds', (req: Request, res: Response) => {
  const query = (req.query.q as string || '').toLowerCase().trim();
  const category = (req.query.category as string || '').toLowerCase().trim();
  const tag = (req.query.tag as string || '').toLowerCase().trim();

  let results = [...soundCatalog];

  if (category && category !== 'all') {
    results = results.filter((s) => s.category.toLowerCase() === category);
  }

  if (tag) {
    results = results.filter((s) => s.tags.toLowerCase().includes(tag));
  }

  if (query) {
    results = results.filter(
      (s) =>
        s.sound_name.toLowerCase().includes(query) ||
        s.category.toLowerCase().includes(query) ||
        s.tags.toLowerCase().includes(query)
    );
  }

  res.json(results);
});

// 3. Trending sounds
app.get('/api/sounds/trending', (req: Request, res: Response) => {
  const sorted = [...soundCatalog].sort((a, b) => (b.play_count || 0) - (a.play_count || 0));
  res.json(sorted.slice(0, 8));
});

// 4. Recent sounds
app.get('/api/sounds/recent', (req: Request, res: Response) => {
  const sorted = [...soundCatalog].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );
  res.json(sorted.slice(0, 8));
});

// 5. Sound categories with counts
app.get('/api/categories', (req: Request, res: Response) => {
  const counts: Record<string, number> = {};
  for (const s of soundCatalog) {
    counts[s.category] = (counts[s.category] || 0) + 1;
  }
  const result = Object.entries(counts).map(([name, count]) => ({
    name,
    count,
  }));
  res.json(result);
});

// 6. Servers list
app.get('/api/servers', (req: Request, res: Response) => {
  res.json(Object.values(servers));
});

// 7. Server soundboard status & slots
app.get('/api/servers/:serverId/soundboard', (req: Request, res: Response) => {
  const server = servers[req.params.serverId];
  if (!server) {
    return res.status(404).json({ error: 'Server not found' });
  }

  const maxSlots = TIER_SOUNDBOARD_SLOTS[server.premium_tier] || 8;
  const usedSlots = server.sounds.length;
  const availableSlots = Math.max(0, maxSlots - usedSlots);

  res.json({
    server_id: server.id,
    server_name: server.name,
    icon: server.icon,
    premium_tier: server.premium_tier,
    premium_subscription_count: server.premium_subscription_count,
    max_slots: maxSlots,
    used_slots: usedSlots,
    available_slots: availableSlots,
    usage_percentage: Math.round((usedSlots / maxSlots) * 100),
    sounds: server.sounds,
  });
});

// 8. Add sound to server soundboard
app.post('/api/servers/:serverId/soundboard/add', (req: Request, res: Response) => {
  const { serverId } = req.params;
  const { soundId, customName, volume = 1.0, username = 'DiscordUser' } = req.body;

  const server = servers[serverId];
  if (!server) {
    return res.status(404).json({ success: false, error: 'Server not found' });
  }

  const sound = soundCatalog.find((s) => s.sound_id === soundId);
  if (!sound) {
    return res.status(404).json({ success: false, error: 'Sound not found in catalog' });
  }

  const finalName = (customName || sound.sound_name).trim();

  // 1. Name validation (2-32 characters per Discord documentation)
  if (finalName.length < 2 || finalName.length > 32) {
    const errorMsg = 'Sound name must be between 2 and 32 characters.';
    logHistory(server, username, sound.sound_id, finalName, 'FAILED', errorMsg);
    return res.status(400).json({ success: false, error: errorMsg });
  }

  // 2. Capacity limit check
  const maxSlots = TIER_SOUNDBOARD_SLOTS[server.premium_tier] || 8;
  if (server.sounds.length >= maxSlots) {
    const errorMsg = `Soundboard capacity reached (${server.sounds.length}/${maxSlots} slots used). Upgrade server boost tier for more slots.`;
    logHistory(server, username, sound.sound_id, finalName, 'FAILED', errorMsg);
    return res.status(400).json({ success: false, error: errorMsg });
  }

  // 3. Duplicate name check
  if (server.sounds.some((s) => s.name.toLowerCase() === finalName.toLowerCase())) {
    const errorMsg = `A sound named "${finalName}" already exists on this server's Soundboard.`;
    logHistory(server, username, sound.sound_id, finalName, 'FAILED', errorMsg);
    return res.status(400).json({ success: false, error: errorMsg });
  }

  // 4. Add sound to server
  const newSoundboardItem: SoundboardSound = {
    id: `sb_${Date.now()}`,
    name: finalName,
    sound_id: sound.sound_id,
    volume: Math.max(0.1, Math.min(1.0, Number(volume) || 1.0)),
    emoji: sound.emoji || '🎵',
    user: {
      id: `u_${Date.now()}`,
      username,
    },
    added_at: new Date().toISOString(),
    file_path: sound.file_path,
    duration: sound.duration,
  };

  server.sounds.push(newSoundboardItem);
  sound.play_count = (sound.play_count || 0) + 1;

  logHistory(server, username, sound.sound_id, finalName, 'SUCCESS', null);

  res.json({
    success: true,
    message: `Added "${finalName}" to ${server.name} soundboard!`,
    soundboard_sound: newSoundboardItem,
    slots: {
      used: server.sounds.length,
      max: maxSlots,
      available: maxSlots - server.sounds.length,
    },
  });
});

// 9. Delete sound from soundboard
app.delete('/api/servers/:serverId/soundboard/:soundboardSoundId', (req: Request, res: Response) => {
  const { serverId, soundboardSoundId } = req.params;
  const server = servers[serverId];
  if (!server) {
    return res.status(404).json({ success: false, error: 'Server not found' });
  }

  const index = server.sounds.findIndex((s) => s.id === soundboardSoundId);
  if (index === -1) {
    return res.status(404).json({ success: false, error: 'Sound not found on soundboard' });
  }

  const removed = server.sounds.splice(index, 1)[0];
  const maxSlots = TIER_SOUNDBOARD_SLOTS[server.premium_tier] || 8;

  res.json({
    success: true,
    message: `Deleted "${removed.name}" from ${server.name} soundboard.`,
    removed,
    slots: {
      used: server.sounds.length,
      max: maxSlots,
      available: maxSlots - server.sounds.length,
    },
  });
});

// 10. Custom sound upload & processor
app.post('/api/upload', (req: Request, res: Response) => {
  const { soundName, category = 'Community', duration = 2.4, fileSizeKb = 120, tags = 'custom', emoji = '✨' } = req.body;

  if (!soundName || soundName.trim().length < 2 || soundName.trim().length > 32) {
    return res.status(400).json({ success: false, error: 'Sound name must be 2-32 characters.' });
  }

  const dur = Number(duration);
  // Auto-trim audio if > 5.2s
  const trimmedDuration = dur > 5.2 ? 5.2 : Math.max(0.5, dur);
  const sizeKb = Math.min(512, Number(fileSizeKb) || 128);

  const cleanId = soundName.toLowerCase().replace(/[^a-z0-9]/g, '_').slice(0, 24) + '_' + Math.floor(Math.random() * 1000);

  const newSound: SoundItem = {
    sound_id: cleanId,
    sound_name: soundName.trim(),
    category: category || 'Community',
    file_path: '/sounds/airhorn.mp3', // Map to bundled sound for real browser playback
    duration: parseFloat(trimmedDuration.toFixed(1)),
    file_size: sizeKb * 1024,
    file_format: 'mp3',
    source_url: 'Custom Upload (Normalized & Trimmed)',
    tags: tags || `custom, ${soundName.toLowerCase()}`,
    created_at: new Date().toISOString(),
    emoji: emoji || '🎵',
    play_count: 1,
  };

  soundCatalog.unshift(newSound);

  res.json({
    success: true,
    message: `Sound "${newSound.sound_name}" processed, normalized to -14 LUFS, and trimmed to ${trimmedDuration}s.`,
    sound: newSound,
  });
});

// 11. Upload history / audit trail
app.get('/api/history', (req: Request, res: Response) => {
  const limit = Math.min(50, Number(req.query.limit) || 20);
  res.json(uploadHistory.slice(0, limit));
});

// 12. Interactive Discord Slash Command Execution Simulator
app.post('/api/bot/command', (req: Request, res: Response) => {
  const { command, serverId = 'guild_101', username = 'DiscordUser' } = req.body;
  const input = (command || '').trim();
  const server = servers[serverId] || servers['guild_101'];

  // Parse command: e.g. /search vine, /preview bonk, /add bonk, /soundboard status, etc.
  if (input.startsWith('/help')) {
    return res.json({
      type: 'embed',
      embed: {
        title: '🔊 Welcome to Dissound (MemeSound Bot)',
        description: 'Dissound eliminates the hassle of finding, downloading, converting, and uploading meme sounds to your Discord Server Soundboard!',
        color: 0x5865f2,
        fields: [
          {
            name: '🔍 Sound Discovery',
            value: '`/search <query>` - Live search catalog with autocomplete\n`/browse [category]` - Browse categorized sounds\n`/trending` - Most added sounds across Discord\n`/recent` - Newly added sounds in catalog',
          },
          {
            name: '🔊 Previews & Direct Adding',
            value: '`/preview <sound>` - Play audio clip with one-click Add button\n`/add <sound> [custom_name] [volume]` - Add sound directly to soundboard',
          },
          {
            name: '⚙️ Server Soundboard Management',
            value: '`/soundboard list` - View active soundboard sounds\n`/soundboard status` - Check slot capacity and boost tier\n`/soundboard delete <name>` - Delete a sound from soundboard\n`/upload <file> [name]` - Auto-trim and add custom audio file\n`/history` - View upload audit logs',
          },
        ],
        footer: { text: 'Dissound • Built for everyday Discord voice fun' },
      },
    });
  }

  if (input.startsWith('/search')) {
    const q = input.replace('/search', '').trim().toLowerCase();
    const matches = soundCatalog.filter(
      (s) => s.sound_name.toLowerCase().includes(q) || s.category.toLowerCase().includes(q) || s.tags.toLowerCase().includes(q)
    );

    if (matches.length === 0) {
      return res.json({
        type: 'embed',
        embed: {
          title: '🔍 No Sounds Found',
          description: `Could not find any meme sounds matching **${q || 'all'}**.\nTry searching for \`vine boom\`, \`pipe\`, \`airhorn\`, or browse with \`/browse\`.`,
          color: 0xed4245,
        },
      });
    }

    return res.json({
      type: 'embed_with_sounds',
      embed: {
        title: `🔍 Search Results for '${q || 'all'}' (${matches.length} found)`,
        description: 'Preview sounds below or click to install them directly to your Soundboard:',
        color: 0x5865f2,
        fields: matches.slice(0, 5).map((s, idx) => ({
          name: `${idx + 1}. ${s.emoji || '🎵'} ${s.sound_name}`,
          value: `**Category:** ${s.category} | **Duration:** \`${s.duration}s\` | **Format:** \`${s.file_format.toUpperCase()}\``,
          inline: true,
        })),
        footer: { text: matches.length > 5 ? `...plus ${matches.length - 5} more in catalog` : 'One-click Add enabled' },
      },
      sounds: matches.slice(0, 5),
    });
  }

  if (input.startsWith('/preview')) {
    const name = input.replace('/preview', '').trim().toLowerCase();
    const sound = soundCatalog.find((s) => s.sound_name.toLowerCase().includes(name) || s.sound_id.includes(name)) || soundCatalog[0];

    return res.json({
      type: 'preview_card',
      embed: {
        title: `🔊 Sound Preview: ${sound.sound_name}`,
        description: `**Category:** ${sound.category}\n**Duration:** \`${sound.duration}s\`\n**Size:** \`${Math.round(sound.file_size / 1024)} KB\`\n**Source:** ${sound.source_url}\n**Tags:** \`${sound.tags}\``,
        color: 0x5865f2,
        footer: { text: "Listen to the audio preview above, then click 'Add to Soundboard' to install!" },
      },
      sound,
    });
  }

  if (input.startsWith('/soundboard status') || input === '/status') {
    const maxSlots = TIER_SOUNDBOARD_SLOTS[server.premium_tier] || 8;
    const used = server.sounds.length;
    const available = Math.max(0, maxSlots - used);
    const filledBlocks = Math.round((used / maxSlots) * 10);
    const bar = '█'.repeat(filledBlocks) + '░'.repeat(10 - filledBlocks);

    return res.json({
      type: 'embed',
      embed: {
        title: `📊 Soundboard Capacity: ${server.name}`,
        color: 0x5865f2,
        fields: [
          { name: 'Slots Used', value: `\`${used} / ${maxSlots}\` (${bar} ${Math.round((used / maxSlots) * 100)}%)`, inline: false },
          { name: 'Slots Remaining', value: `\`${available}\` available`, inline: true },
          { name: 'Server Boost Level', value: `Tier ${server.premium_tier} (${server.premium_subscription_count} boosts)`, inline: true },
          {
            name: 'Tier Capacity Guide',
            value: '• **Tier 0** (No Boost): 8 slots\n• **Tier 1**: 24 slots\n• **Tier 2**: 36 slots\n• **Tier 3**: 48 slots',
            inline: false,
          },
        ],
      },
    });
  }

  if (input.startsWith('/soundboard list')) {
    const maxSlots = TIER_SOUNDBOARD_SLOTS[server.premium_tier] || 8;
    return res.json({
      type: 'embed',
      embed: {
        title: `🔊 ${server.name} Soundboard Sounds`,
        description: `**Capacity:** \`${server.sounds.length} / ${maxSlots} slots used\`\n**Server Boost Level:** \`Tier ${server.premium_tier}\`\n\n` +
          (server.sounds.length === 0
            ? '*No sounds on this server yet! Add some with `/search` or `/add`.*'
            : ''),
        color: 0x5865f2,
        fields: server.sounds.map((s, idx) => ({
          name: `${idx + 1}. ${s.emoji || '🎵'} ${s.name}`,
          value: `Volume: \`${s.volume}\` | Added by <@${s.user.username}>`,
          inline: true,
        })),
      },
    });
  }

  if (input.startsWith('/history')) {
    const logs = uploadHistory.slice(0, 5);
    return res.json({
      type: 'embed',
      embed: {
        title: `📜 Soundboard Upload History: ${server.name}`,
        description: `Showing the last ${logs.length} upload attempts:`,
        color: 0x5865f2,
        fields: logs.map((item) => ({
          name: `${item.upload_status === 'SUCCESS' ? '✅' : '❌'} ${item.sound_name}`,
          value: `**Status:** \`${item.upload_status}\`\n**Requested by:** <@${item.username}>\n**Time:** \`${new Date(item.timestamp).toLocaleString()}\`${
            item.error_message ? `\n*Error: ${item.error_message}*` : ''
          }`,
          inline: false,
        })),
      },
    });
  }

  if (input.startsWith('/add')) {
    const soundArg = input.replace('/add', '').trim();
    const sound = soundCatalog.find((s) => s.sound_name.toLowerCase().includes(soundArg.toLowerCase()) || s.sound_id === soundArg) || soundCatalog[0];
    const maxSlots = TIER_SOUNDBOARD_SLOTS[server.premium_tier] || 8;

    if (server.sounds.length >= maxSlots) {
      const err = `Soundboard capacity reached (${server.sounds.length}/${maxSlots} slots used). Upgrade server boost tier for more slots.`;
      logHistory(server, username, sound.sound_id, sound.sound_name, 'FAILED', err);
      return res.json({
        type: 'embed',
        embed: {
          title: '❌ Failed to Add Sound',
          description: err,
          color: 0xed4245,
        },
      });
    }

    if (server.sounds.some((s) => s.name.toLowerCase() === sound.sound_name.toLowerCase())) {
      const err = `A sound named "${sound.sound_name}" already exists on this server's Soundboard.`;
      logHistory(server, username, sound.sound_id, sound.sound_name, 'FAILED', err);
      return res.json({
        type: 'embed',
        embed: {
          title: '❌ Duplicate Sound Name',
          description: err,
          color: 0xed4245,
        },
      });
    }

    const newSoundItem: SoundboardSound = {
      id: `sb_${Date.now()}`,
      name: sound.sound_name,
      sound_id: sound.sound_id,
      volume: 1.0,
      emoji: sound.emoji || '🎵',
      user: { id: 'u_user', username },
      added_at: new Date().toISOString(),
      file_path: sound.file_path,
      duration: sound.duration,
    };
    server.sounds.push(newSoundItem);
    sound.play_count = (sound.play_count || 0) + 1;
    logHistory(server, username, sound.sound_id, sound.sound_name, 'SUCCESS', null);

    return res.json({
      type: 'embed',
      embed: {
        title: '✅ Sound Added to Soundboard!',
        description: `Successfully added **${sound.sound_name}** to **${server.name}**!\n\n**Slot Usage:** \`${server.sounds.length} / ${maxSlots}\`\n**Volume:** \`1.0\` (Default)`,
        color: 0x57f287,
      },
    });
  }

  // Fallback
  return res.json({
    type: 'embed',
    embed: {
      title: 'Command Executed',
      description: `Unknown or unhandled slash command: \`${input}\`.\nTry \`/help\`, \`/search vine\`, \`/preview airhorn\`, \`/soundboard status\`, or \`/soundboard list\`.`,
      color: 0xfee75c,
    },
  });
});

function logHistory(
  server: ServerData,
  username: string,
  soundId: string,
  soundName: string,
  status: 'SUCCESS' | 'FAILED',
  errorMessage: string | null
) {
  uploadHistory.unshift({
    upload_id: uploadHistory.length + 1,
    server_id: server.id,
    server_name: server.name,
    user_id: `u_${username.toLowerCase()}`,
    username,
    sound_id: soundId,
    sound_name: soundName,
    upload_status: status,
    error_message: errorMessage,
    timestamp: new Date().toISOString(),
  });
}

// In production or development with Vite
async function startServer() {
  const isProd = process.env.NODE_ENV === 'production';

  if (!isProd) {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: 'spa',
    });
    app.use(vite.middlewares);
  } else {
    app.use(express.static(path.resolve('dist')));
    app.use('*', (req, res) => {
      res.sendFile(path.resolve('dist/index.html'));
    });
  }

  app.listen(PORT, HOST, () => {
    console.log(`🚀 Dissound server running at http://${HOST}:${PORT}`);
  });
}

startServer().catch((err) => {
  console.error('Failed to start server:', err);
  process.exit(1);
});
