// Common types for the application

export interface User {
  id: number
  username: string
  email: string
  is_active: boolean
  is_verified: boolean
  created_at: string
  updated_at?: string
  last_login?: string
}

export interface Task {
  id: number
  name: string
  description?: string
  departure_city: string
  arrival_city: string
  travel_date: string
  return_date?: string
  num_travelers: number
  cabin_class: string
  task_type: 'one_time' | 'recurring'
  task_validity: 'scheduled' | 'instant'
  scheduled_time?: string
  frequency?: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  created_at: string
  updated_at?: string
  started_at?: string
  completed_at?: string
  error_message?: string
  retry_count: number
  max_retries: number
}

export interface TaskCreate {
  name: string
  description?: string
  departure_city: string
  arrival_city: string
  travel_date: string
  return_date?: string
  num_travelers: number
  cabin_class: string
  task_type: 'one_time' | 'recurring'
  task_validity: 'scheduled' | 'instant'
  scheduled_time?: string
  frequency?: string
}

export interface FlightData {
  id: number
  airline: string
  flight_number: string
  departure_airport: string
  arrival_airport: string
  departure_time: string
  arrival_time: string
  duration?: string
  price: number
  currency: string
  original_price?: number
  discount_amount?: number
  discount_percentage?: number
  stops: number
  aircraft_type?: string
  cabin_class?: string
  promotional_offers?: string
  booking_url?: string
  source_platform: string
  source_account?: string
  scraped_at: string
  is_verified: boolean
  confidence_score: number
}

export interface Platform {
  id: number
  name: string
  display_name: string
  platform_type: 'web' | 'mobile_app'
  base_url?: string
  bundle_id?: string
  package_name?: string
  search_url_template?: string
  selectors?: Record<string, any>
  headers?: Record<string, string>
  is_active: boolean
  created_at: string
  updated_at?: string
}

export interface Account {
  id: number
  platform_id: number
  username: string
  password: string
  email?: string
  max_queries_per_day: number
  current_query_count: number
  last_query_date?: string
  is_active: boolean
  is_verified: boolean
  created_at: string
  updated_at?: string
}

export interface DashboardStats {
  task_stats: {
    total: number
    running: number
    completed: number
    failed: number
    recent_24h: number
  }
  flight_stats: {
    total_flights: number
    unique_airlines: number
    average_price: number
    lowest_price: number
  }
  last_execution_time?: string
  timestamp: string
}

export interface PriceTrend {
  date: string
  average_price: number
  minimum_price: number
  flight_count: number
}

export interface ApiResponse<T> {
  data: T
  message?: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  skip: number
  limit: number
}
