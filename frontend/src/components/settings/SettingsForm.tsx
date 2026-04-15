import { useState } from 'react';
import { Eye, EyeOff, Info } from 'lucide-react';

interface SettingsFormProps {
  openrouterApiKey: string;
  aiModel: string;
  aiTemperature: number;
  tesseractPath: string;
  visionMaxPages: number;
  onOpenRouterApiKeyChange: (value: string) => void;
  onAiModelChange: (value: string) => void;
  onAiTemperatureChange: (value: number) => void;
  onTesseractPathChange: (value: string) => void;
  onVisionMaxPagesChange: (value: number) => void;
  disabled?: boolean;
}

const AI_MODEL_OPTIONS = [
  { value: 'google/gemini-2.0-flash-001', label: 'Google Gemini 2.0 Flash' },
  { value: 'anthropic/claude-3-5-sonnet', label: 'Anthropic Claude 3.5 Sonnet' },
  { value: 'openai/gpt-4', label: 'OpenAI GPT-4' },
];

export default function SettingsForm({
  openrouterApiKey,
  aiModel,
  aiTemperature,
  tesseractPath,
  visionMaxPages,
  onOpenRouterApiKeyChange,
  onAiModelChange,
  onAiTemperatureChange,
  onTesseractPathChange,
  onVisionMaxPagesChange,
  disabled = false,
}: SettingsFormProps) {
  const [showApiKey, setShowApiKey] = useState(false);

  return (
    <div className="space-y-6">
      {/* OpenRouter API Key */}
      <div>
        <label htmlFor="openrouter-api-key" className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
          OpenRouter API Key *
        </label>
        <div className="relative">
          <input
            id="openrouter-api-key"
            type={showApiKey ? 'text' : 'password'}
            value={openrouterApiKey}
            onChange={(e) => onOpenRouterApiKeyChange(e.target.value)}
            disabled={disabled}
            placeholder="sk-or-v1-..."
            className="block w-full rounded-md border border-gray-300 bg-white px-3 py-2 pr-10 text-sm placeholder-gray-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:cursor-not-allowed disabled:bg-gray-50 disabled:text-gray-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-200 dark:placeholder-gray-500 dark:disabled:bg-gray-800 dark:disabled:text-gray-500"
          />
          <button
            type="button"
            onClick={() => setShowApiKey(!showApiKey)}
            className="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300"
            disabled={disabled}
          >
            {showApiKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          </button>
        </div>
        <div className="mt-1 flex items-start gap-1.5 text-xs text-gray-500 dark:text-gray-400">
          <Info className="mt-0.5 h-3.5 w-3.5 flex-shrink-0" />
          <p>API key pentru serviciul OpenRouter (AI classification)</p>
        </div>
      </div>

      {/* AI Model */}
      <div>
        <label htmlFor="ai-model" className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
          Model AI *
        </label>
        <select
          id="ai-model"
          value={aiModel}
          onChange={(e) => onAiModelChange(e.target.value)}
          disabled={disabled}
          className="block w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:cursor-not-allowed disabled:bg-gray-50 disabled:text-gray-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-200 dark:disabled:bg-gray-800 dark:disabled:text-gray-500"
        >
          {AI_MODEL_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        <div className="mt-1 flex items-start gap-1.5 text-xs text-gray-500 dark:text-gray-400">
          <Info className="mt-0.5 h-3.5 w-3.5 flex-shrink-0" />
          <p>Modelul AI folosit pentru clasificare</p>
        </div>
      </div>

      {/* AI Temperature */}
      <div>
        <label htmlFor="ai-temperature" className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
          Temperatură AI *
        </label>
        <div className="flex items-center gap-3">
          <input
            id="ai-temperature"
            type="range"
            min="0"
            max="1"
            step="0.1"
            value={aiTemperature}
            onChange={(e) => onAiTemperatureChange(parseFloat(e.target.value))}
            disabled={disabled}
            className="flex-1 accent-blue-600 disabled:cursor-not-allowed disabled:opacity-50"
          />
          <input
            type="number"
            min="0"
            max="1"
            step="0.1"
            value={aiTemperature}
            onChange={(e) => onAiTemperatureChange(parseFloat(e.target.value))}
            disabled={disabled}
            className="w-20 rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-center focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:cursor-not-allowed disabled:bg-gray-50 disabled:text-gray-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-200 dark:disabled:bg-gray-800 dark:disabled:text-gray-500"
          />
        </div>
        <div className="mt-1 flex items-start gap-1.5 text-xs text-gray-500 dark:text-gray-400">
          <Info className="mt-0.5 h-3.5 w-3.5 flex-shrink-0" />
          <p>Temperatura pentru generarea răspunsurilor AI (0 = deterministic, 1 = creativ)</p>
        </div>
      </div>

      {/* Tesseract Path */}
      <div>
        <label htmlFor="tesseract-path" className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
          Calea către Tesseract
        </label>
        <input
          id="tesseract-path"
          type="text"
          value={tesseractPath}
          onChange={(e) => onTesseractPathChange(e.target.value)}
          disabled={disabled}
          placeholder="D:\Tesseract-OCR\tesseract.exe"
          className="block w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm placeholder-gray-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:cursor-not-allowed disabled:bg-gray-50 disabled:text-gray-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-200 dark:placeholder-gray-500 dark:disabled:bg-gray-800 dark:disabled:text-gray-500"
        />
        <div className="mt-1 flex items-start gap-1.5 text-xs text-gray-500 dark:text-gray-400">
          <Info className="mt-0.5 h-3.5 w-3.5 flex-shrink-0" />
          <p>Calea completă către executabilul Tesseract OCR</p>
        </div>
      </div>

      {/* Vision Max Pages */}
      <div>
        <label htmlFor="vision-max-pages" className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
          Pagini maxime pentru Vision AI *
        </label>
        <input
          id="vision-max-pages"
          type="number"
          min="1"
          max="10"
          value={visionMaxPages}
          onChange={(e) => onVisionMaxPagesChange(parseInt(e.target.value, 10))}
          disabled={disabled}
          className="block w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:cursor-not-allowed disabled:bg-gray-50 disabled:text-gray-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-200 dark:disabled:bg-gray-800 dark:disabled:text-gray-500"
        />
        <div className="mt-1 flex items-start gap-1.5 text-xs text-gray-500 dark:text-gray-400">
          <Info className="mt-0.5 h-3.5 w-3.5 flex-shrink-0" />
          <p>Numărul maxim de pagini procesate cu Vision AI (fallback pentru OCR)</p>
        </div>
      </div>
    </div>
  );
}
