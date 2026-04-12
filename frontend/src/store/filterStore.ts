import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { DocumentCategory, ProcessingStatus, ReviewStatus } from '../types';

interface FilterState {
  categories: DocumentCategory[];
  processingStatus: ProcessingStatus | '';
  reviewStatus: ReviewStatus | '';
  search: string;
  setCategories: (categories: DocumentCategory[]) => void;
  setProcessingStatus: (status: ProcessingStatus | '') => void;
  setReviewStatus: (status: ReviewStatus | '') => void;
  setSearch: (search: string) => void;
  resetFilters: () => void;
}

export const useFilterStore = create<FilterState>()(
  persist(
    (set) => ({
      categories: [],
      processingStatus: '',
      reviewStatus: '',
      search: '',
      setCategories: (categories) => set({ categories }),
      setProcessingStatus: (processingStatus) => set({ processingStatus }),
      setReviewStatus: (reviewStatus) => set({ reviewStatus }),
      setSearch: (search) => set({ search }),
      resetFilters: () =>
        set({ categories: [], processingStatus: '', reviewStatus: '', search: '' }),
    }),
    { name: 'makyol-filters' }
  )
);
