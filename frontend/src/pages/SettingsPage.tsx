import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Settings, Save, FileText } from 'lucide-react';
import toast from 'react-hot-toast';
import SettingsForm from '../components/settings/SettingsForm';
import { useSettingsStore } from '../store/settingsStore';
import { listSettings, updateSetting } from '../api/settings';

export default function SettingsPage() {
  const [isSaving, setIsSaving] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  const {
    openrouter_api_key,
    ai_model,
    ai_temperature,
    tesseract_path,
    vision_max_pages,
    setOpenRouterApiKey,
    setAiModel,
    setAiTemperature,
    setTesseractPath,
    setVisionMaxPages,
    updateSettings,
  } = useSettingsStore();

  // Load settings from backend on mount
  useEffect(() => {
    const loadSettings = async () => {
      try {
        const response = await listSettings();
        const settingsMap = response.data.reduce(
          (acc, setting) => {
            acc[setting.key] = setting.value;
            return acc;
          },
          {} as Record<string, any>,
        );

        // Update store with backend values
        updateSettings({
          openrouter_api_key: settingsMap.openrouter_api_key ?? openrouter_api_key,
          ai_model: settingsMap.ai_model ?? ai_model,
          ai_temperature: settingsMap.ai_temperature ?? ai_temperature,
          tesseract_path: settingsMap.tesseract_path ?? tesseract_path,
          vision_max_pages: settingsMap.vision_max_pages ?? vision_max_pages,
        });
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Eroare la încărcarea setărilor';
        toast.error(message);
      } finally {
        setIsLoading(false);
      }
    };

    loadSettings();
  }, []);

  const handleSave = async () => {
    setIsSaving(true);

    try {
      // Save all settings to backend
      await Promise.all([
        updateSetting('openrouter_api_key', openrouter_api_key),
        updateSetting('ai_model', ai_model),
        updateSetting('ai_temperature', ai_temperature),
        updateSetting('tesseract_path', tesseract_path),
        updateSetting('vision_max_pages', vision_max_pages),
      ]);

      toast.success('Setările au fost salvate cu succes');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Eroare la salvarea setărilor';
      toast.error(message);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Settings className="h-6 w-6 text-gray-700 dark:text-gray-300" />
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Setări</h1>
        </div>
        <Link
          to="/documents"
          className="flex items-center gap-2 rounded-lg bg-gray-100 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-200 transition-colors dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600"
        >
          <FileText className="h-4 w-4" />
          Vezi toate documentele
        </Link>
      </div>

      <div className="mx-auto max-w-2xl">
        <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-gray-200 border-t-blue-600" />
            </div>
          ) : (
            <>
              <SettingsForm
                openrouterApiKey={openrouter_api_key}
                aiModel={ai_model}
                aiTemperature={ai_temperature}
                tesseractPath={tesseract_path}
                visionMaxPages={vision_max_pages}
                onOpenRouterApiKeyChange={setOpenRouterApiKey}
                onAiModelChange={setAiModel}
                onAiTemperatureChange={setAiTemperature}
                onTesseractPathChange={setTesseractPath}
                onVisionMaxPagesChange={setVisionMaxPages}
                disabled={isSaving}
              />

              <div className="mt-6 flex justify-end gap-3">
                <button
                  onClick={handleSave}
                  disabled={isSaving}
                  className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 transition-colors disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <Save className="h-4 w-4" />
                  {isSaving ? 'Se salvează...' : 'Salvează setările'}
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
