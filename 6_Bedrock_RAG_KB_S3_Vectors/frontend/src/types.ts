export interface QueryResponse {
  query: string;
  generated_response: string;
  s3_locations: string[];
}

export interface QueryError {
  error: string;
}
