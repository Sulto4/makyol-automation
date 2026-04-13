import apiClient from './client';
import type {
  SettingsListResponse,
  SettingResponse,
  UpdateSettingResponse,
  UpdateSettingInput,
} from '../types';

/**
 * Fetch all settings
 */
export async function listSettings(): Promise<SettingsListResponse> {
  const { data } = await apiClient.get<SettingsListResponse>('/settings');
  return data;
}

/**
 * Fetch a single setting by key
 */
export async function getSetting(key: string): Promise<SettingResponse> {
  const { data } = await apiClient.get<SettingResponse>(`/settings/${key}`);
  return data;
}

/**
 * Update or create a setting (upsert)
 *
 * @param key - The setting key
 * @param value - The setting value to update
 */
export async function updateSetting(
  key: string,
  value: UpdateSettingInput['value'],
): Promise<UpdateSettingResponse> {
  const { data } = await apiClient.put<UpdateSettingResponse>(
    `/settings/${key}`,
    { value },
  );
  return data;
}
