export interface SoundItem {
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

export interface SoundboardSound {
  id: string;
  name: string;
  sound_id: string;
  volume: number;
  emoji?: string;
  user: {
    id: string;
    username: string;
  };
  added_at: string;
  file_path: string;
  duration: number;
}

export interface ServerData {
  id: string;
  name: string;
  icon: string;
  premium_tier: number;
  premium_subscription_count: number;
  sound_limit: number;
  sounds: SoundboardSound[];
}

export interface UploadHistoryItem {
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

export interface BotInfo {
  status: string;
  name: string;
  version: string;
  discord_py: string;
  total_sounds: number;
  active_servers: number;
  bot_permissions: string[];
  supported_audio_specs: {
    max_duration_sec: number;
    max_file_size_kb: number;
    supported_formats: string[];
    sound_name_length: string;
    volume_range: string;
  };
  tier_limits: Record<number, number>;
}
