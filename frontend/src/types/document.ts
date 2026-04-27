export interface Document {
  id: number
  title: string
  authors: string
  year: number
  abstract?: string
  keywords?: string
  category?: string
  publisher?: string
  isbn?: string
  udk?: string
  bbk?: string
  rubrics?: string
  source_url?: string
  source_system?: string
  external_id?: string
  has_fulltext?: number
}

export interface PopularDocument {
  id: number
  title: string
  authors: string
  year: number
  category: string
  interactions_count: number
}
