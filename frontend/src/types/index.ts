export interface UserSummary {
  id: string
  display_name: string
}

export interface UserProfile extends UserSummary {
  email?: string
  follower_count: number
  following_count: number
  is_following?: boolean
  date_joined?: string
}

export interface ListProgress {
  exploration_id: string | null
  viewed_count: number
  total_count: number
  percentage: number
  completed_count: number
}

export interface QuestionList {
  id: string
  owner: UserSummary
  name: string
  description: string
  visibility: "public" | "private"
  question_count: number
  subscriber_count: number
  visitor_count: number
  current_user_role: "owner" | "administrator" | "contributor" | null
  is_subscribed: boolean
  progress: ListProgress | null
  created_at: string
  updated_at: string
}

export interface Question {
  id: string
  question_list_id: string
  author: UserSummary
  text: string
  image: string | null
  position: number
  created_at: string
  updated_at: string
}

export interface Collaboration {
  id: string
  user: UserSummary
  role: "contributor" | "administrator"
  created_at: string
  updated_at: string
}

export interface DiscoveryHome {
  followed_lists: QuestionList[]
  followed_users: UserProfile[]
  discover: QuestionList[]
}

export interface GlobalSearchResults {
  query: string
  lists: QuestionList[]
  users: UserProfile[]
}

export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface PickQuestionResponse {
  question: Question
  exploration_id: string
  progress: {
    viewed_count: number
    total_count: number
    percentage: number
  }
  list_progress: {
    viewed_count: number
    total_count: number
    percentage: number
  }
  session_completed: boolean
  list_completed: boolean
}

export function unwrapResults<T>(data: PaginatedResponse<T> | T[]): T[] {
  return Array.isArray(data) ? data : data.results
}
