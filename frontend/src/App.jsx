import { useState } from 'react'
import styled, { createGlobalStyle } from 'styled-components'
import Logo from './components/Logo'
import { getMovieRecommendations } from './services/api'

const GlobalStyle = createGlobalStyle`
  body {
    margin: 0;
    padding: 0;
    background-color: #1a1d21;
  }
`

const ErrorMessage = styled.div`
  color: #ff4444;
  margin: 10px 0;
`

const MovieResult = styled.div`
  padding: 20px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  width: 165px;
  
  .poster-link {
    display: block;
    &:hover {
      opacity: 0.8;
      transition: opacity 0.2s;
    }
  }

  .poster {
    width: 125px;
    height: 187px;
    border-radius: 4px;
    object-fit: cover;
  }

  .movie-info {
    text-align: center;
    width: 100%;
  }
  
  h2 {
    color: rgb(219, 224, 255);
    margin: 0;
    font-size: 14px;
    
    a {
      color: inherit;
      text-decoration: none;
      &:hover {
        text-decoration: underline;
      }
    }
  }
`

const Container = styled.div`
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  color: #99aabb;
  padding: 20px;
`

const MainContent = styled.div`
  text-align: center;
  max-width: 800px;
  width: 100%;
  margin-top: 40px;
`

const ResultHeader = styled.h1`
  color: rgb(219, 224, 255);
  font-size: 24px;
  margin-bottom: 30px;
  text-align: center;
  width: 100%;
`

const ResultContainer = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  justify-content: center;
  max-width: 1200px;
  width: 100%;
  margin: 40px auto;
  padding: 0 20px;
`

const Instructions = styled.p`
  margin-bottom: 20px;
  line-height: 1.4;

  a {
    color: #99aabb;
    text-decoration: None;
    &:hover {
      text-decoration: underline;
    }
  }
`

const InputContainer = styled.div`
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
`

const Input = styled.input`
  flex: 1;
  padding: 12px 16px;
  border-radius: 4px;
  border: none;
  background-color:rgb(207, 222, 245);
  color: #1a1d21;
  font-size: 16px;

  &::placeholder {
    color: #999;
  }
`

const SubmitButton = styled.button`
  padding: 12px 24px;
  border-radius: 4px;
  border: none;
  background-color:rgb(88, 109, 135);
  color: rgb(218, 227, 241);
  font-size: 16px;
  cursor: pointer;
  transition: background-color 0.2s;

  &:hover {
    background-color: #678;
  }
`

const Select = styled.select`
  padding: 12px 16px;
  border-radius: 4px;
  border: none;
  background-color: rgb(207, 222, 245);
  color: #1a1d21;
  font-size: 16px;
  cursor: pointer;
`

const AdvancedOptions = styled.button`  background: none;
  border: none;
  color: #567;
  cursor: pointer;
  font-size: 14px;
  padding: 0;
  margin-top: 10px;

  &:hover {
    color: #678;
    text-decoration: underline;
  }
`

const SavedMoviesPanel = styled.div`
  position: fixed;
  right: ${props => props.isExpanded ? '0' : '-320px'};
  top: 0;
  width: 320px;
  height: 100vh;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  transition: right 0.3s ease;
  padding: 20px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 20px;
  z-index: 100;

  .toggle-button {
    position: absolute;
    left: -40px;
    top: 50%;
    transform: translateY(-50%);
    background: rgba(255, 255, 255, 0.1);
    border: none;
    color: rgb(219, 224, 255);
    padding: 10px;
    cursor: pointer;
    border-radius: 4px 0 0 4px;
    backdrop-filter: blur(10px);
    
    &:hover {
      background: rgba(255, 255, 255, 0.2);
    }
  }

  h2 {
    color: rgb(219, 224, 255);
    margin: 0;
    font-size: 18px;
  }

  .saved-movies-list {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 10px;
    overflow-y: auto;
  }

  .saved-movie {
    display: flex;
    align-items: center;
    gap: 10px;
    background: rgba(255, 255, 255, 0.05);
    padding: 10px;
    border-radius: 4px;
    position: relative;

    img {
      width: 40px;
      height: 60px;
      border-radius: 2px;
      object-fit: cover;
    }

    .title {
      flex: 1;
      font-size: 14px;
      color: rgb(219, 224, 255);
    }

    .remove {
      background: none;
      border: none;
      color: #ff4444;
      cursor: pointer;
      padding: 4px;
      font-size: 18px;
      opacity: 0.7;
      
      &:hover {
        opacity: 1;
      }
    }
  }
`

function App() {
  const [usernames, setUsernames] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [movies, setMovies] = useState([])
  const [numMovies, setNumMovies] = useState(1)
  const [savedMovies, setSavedMovies] = useState([])
  const [isPanelExpanded, setIsPanelExpanded] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setMovies([])
    try {
        const result = await getMovieRecommendations(usernames, numMovies)
        setMovies(result || [])
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
    }
  }

  const handleDragStart = (e, movie) => {
    e.dataTransfer.setData('movie', JSON.stringify(movie))
  }

  const handleDragOver = (e) => {
    e.preventDefault()
  }

  const handleDrop = (e) => {
    e.preventDefault()
    try {
      const movie = JSON.parse(e.dataTransfer.getData('movie'))
      if (savedMovies.length < 5 && !savedMovies.some(m => m.id === movie.id)) {
        setSavedMovies([...savedMovies, movie])
      }
    } catch (err) {
      console.error('Failed to add movie:', err)
    }
  }

  const removeSavedMovie = (movieId) => {
    setSavedMovies(savedMovies.filter(m => m.id !== movieId))
  }

  return (
    <>
      <GlobalStyle />
      <Container>
        <div>
          <Logo />
          <MainContent>
            <Instructions>
              Enter up to 5 usernames belonging to public <a href="https://letterboxd.com" target="_blank" rel="noopener noreferrer">Letterboxd</a> profiles to get random films from their watchlists.
              Add multiple usernames by separating them with a space.
            </Instructions>

            <form onSubmit={handleSubmit}>
              <InputContainer>
                <Input
                  type="text"
                  value={usernames} 
                  onChange={(e) => setUsernames(e.target.value)}
                  placeholder="ex: username1 username2"
                  disabled={loading}
                />
                <SubmitButton type="submit" disabled={loading}>
                  {loading ? 'LOADING...' : 'GET'}
                </SubmitButton>
                <Select 
                  value={numMovies} 
                  onChange={(e) => setNumMovies(Number(e.target.value))}
                  disabled={loading}
                >
                  {[1, 2, 3, 4, 5].map(num => (
                    <option key={num} value={num}>
                      {num} {num === 1 ? 'Movie' : 'Movies'}
                    </option>
                  ))}
                </Select>
              </InputContainer>
            </form>

            {error && <ErrorMessage>{error}</ErrorMessage>}

            <AdvancedOptions>
              Advanced Options
            </AdvancedOptions>
          </MainContent>
        </div>

        <ResultContainer>
          {movies.length > 0 && (
            <ResultHeader>Some options for you</ResultHeader>
          )}
          {movies.map((movie, index) => (
            <MovieResult 
              key={movie.id}
              draggable
              onDragStart={(e) => handleDragStart(e, movie)}
            >
              {movie.image_data && (
                <a 
                  href={movie.url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="poster-link"
                >
                  <img 
                    src={movie.image_data}
                    alt={`${movie.title} poster`}
                    className="poster"
                    onError={(e) => {
                      console.error('Image failed to load:', movie.image_data);
                      e.target.style.display = 'none';
                    }}
                  />
                </a>
              )}
              <div className="movie-info">
                <h2>
                  <a href={movie.url} target="_blank" rel="noopener noreferrer">
                    {movie.title.length > 50 ? `${movie.title.slice(0, 50)}...` : movie.title}
                  </a>
                </h2>
              </div>
            </MovieResult>
          ))}
        </ResultContainer>

        <SavedMoviesPanel 
          isExpanded={isPanelExpanded}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
        >
          <button 
            className="toggle-button"
            onClick={() => setIsPanelExpanded(!isPanelExpanded)}
          >
            {isPanelExpanded ? '→' : '←'}
          </button>
          <h2>Saved Movies ({savedMovies.length}/5)</h2>
          <div className="saved-movies-list">
            {savedMovies.map(movie => (
              <div key={movie.id} className="saved-movie">
                {movie.image_data && (
                  <img 
                    src={movie.image_data}
                    alt={`${movie.title} poster`}
                  />
                )}
                <span className="title">
                  {movie.title.length > 30 ? `${movie.title.slice(0, 30)}...` : movie.title}
                </span>
                <button 
                  className="remove"
                  onClick={() => removeSavedMovie(movie.id)}
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        </SavedMoviesPanel>
      </Container>
    </>
  )
}

export default App 
