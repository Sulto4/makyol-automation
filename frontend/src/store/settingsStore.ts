import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface SettingsState {
  openrouter_api_key: string;
  ai_model: string;
  ai_temperature: number;
  tesseract_path: string;
  vision_max_pages: number;
  setOpenRouterApiKey: (key: string) => void;
  setAiModel: (model: string) => void;
  setAiTemperature: (temperature: number) => void;
  setTesseractPath: (path: string) => void;
  setVisionMaxPages: (pages: number) => void;
  updateSettings: (settings: Partial<Omit<SettingsState, 'setOpenRouterApiKey' | 'setAiModel' | 'setAiTemperature' | 'setTesseractPath' | 'setVisionMaxPages' | 'updateSettings' | 'resetSettings'>>) => void;
  resetSettings: () => void;
}

const defaultSettings = {
  openrouter_api_key: '',
  ai_model: 'google/gemini-2.0-flash-001',
  ai_temperature: 0.0,
  tesseract_path: 'D:\\Tesseract-OCR\\tesseract.exe',
  vision_max_pages: 3,
};

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      ...defaultSettings,
      setOpenRouterApiKey: (openrouter_api_key) => set({ openrouter_api_key }),
      setAiModel: (ai_model) => set({ ai_model }),
      setAiTemperature: (ai_temperature) => set({ ai_temperature }),
      setTesseractPath: (tesseract_path) => set({ tesseract_path }),
      setVisionMaxPages: (vision_max_pages) => set({ vision_max_pages }),
      updateSettings: (settings) => set(settings),
      resetSettings: () => set(defaultSettings),
    }),
    { name: 'makyol-settings' }
  )
);
