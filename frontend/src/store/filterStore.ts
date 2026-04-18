import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { DocumentCategory, ProcessingStatus, ReviewStatus } from '../types';

type SortField =
  | 'filename'
  | 'categorie'
  | 'material'
  | 'producator'
  | 'companie'
  | 'distribuitor'
  | 'data_expirare'
  | 'page_count'
  | 'confidence'
  | 'processing_status'
  | 'review_status'
  | 'uploaded_at';
type SortDirection = 'asc' | 'desc';

interface FilterState {
  categories: DocumentCategory[];
  processingStatus: ProcessingStatus | '';
  reviewStatus: ReviewStatus | '';
  search: string;
  currentPage: number;
  perPage: number;
  sortField: SortField;
  sortDirection: SortDirection;
  setCategories: (categories: DocumentCategory[]) => void;
  setProcessingStatus: (status: ProcessingStatus | '') => void;
  setReviewStatus: (status: ReviewStatus | '') => void;
  setSearch: (search: string) => void;
  setCurrentPage: (page: number) => void;
  setPerPage: (perPage: number) => void;
  setSortField: (field: SortField) => void;
  setSortDirection: (dir: SortDirection) => void;
  resetFilters: () => void;
}

export const useFilterStore = create<FilterState>()(
  persist(
    (set) => ({
      categories: [],
      processingStatus: '',
      reviewStatus: '',
      search: '',
      currentPage: 1,
      perPage: 20,
      sortField: 'uploaded_at' as SortField,
      sortDirection: 'desc' as SortDirection,
      setCategories: (categories) => set({ categories, currentPage: 1 }),
      setProcessingStatus: (processingStatus) => set({ processingStatus, currentPage: 1 }),
      setReviewStatus: (reviewStatus) => set({ reviewStatus, currentPage: 1 }),
      setSearch: (search) => set({ search, currentPage: 1 }),
      setCurrentPage: (currentPage) => set({ currentPage }),
      setPerPage: (perPage) => set({ perPage, currentPage: 1 }),
      setSortField: (sortField) => set({ sortField }),
      setSortDirection: (sortDirection) => set({ sortDirection }),
      resetFilters: () =>
        set({ categories: [], processingStatus: '', reviewStatus: '', search: '', currentPage: 1 }),
    }),
    { name: 'makyol-filters' }
  )
);
