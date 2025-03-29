const API_URL = 'http://localhost:8000/api';

export async function getMovieRecommendations(usernames, numMovies = 1, excludeIds = []) {
  const response = await fetch(`${API_URL}/movies`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      usernames: usernames.split(/[\s]+/).filter(u => u),
      exclude_ids: excludeIds,
      num_movies: numMovies
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to get movie recommendations');
  }

  return response.json();
}