/**
 * Reads errors thrown by the generated API client (ApiError) without importing the class,
 * which the client package does not re-export.
 */
export interface ReadableApiError {
  status: number | null;
  message: string;
  correlationId: string | null;
}

export function getStatus(error: unknown): number | null {
  if (error && typeof error === 'object' && 'status' in error) {
    const status = (error as { status: unknown }).status;
    return typeof status === 'number' ? status : null;
  }
  return null;
}

export function readApiError(error: unknown): ReadableApiError {
  const status = getStatus(error);
  let message = 'The request could not be completed.';
  let correlationId: string | null = null;
  if (error && typeof error === 'object') {
    const data = (error as { data?: unknown }).data;
    if (data && typeof data === 'object') {
      const d = data as { message?: unknown; correlationId?: unknown };
      if (typeof d.message === 'string' && d.message) message = d.message;
      if (typeof d.correlationId === 'string' && d.correlationId)
        correlationId = d.correlationId;
    } else if (status === null && error instanceof Error && error.message) {
      message = 'The server could not be reached. ' + error.message;
    }
  }
  return { status, message, correlationId };
}
