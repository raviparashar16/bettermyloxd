import { useState, useEffect } from 'react'
import styled, { createGlobalStyle } from 'styled-components'
import Logo from './components/Logo'
import { getMovieRecommendations } from './services/api'
import bearGif from './components/bear.gif'
import jarvisGif from './components/jarvis.gif'
import gamblingGif from './components/gambling.gif'

const GlobalStyle = createGlobalStyle`
  body {
    margin: 0;
    padding: 0;
    background-color: #1a1d21;
  }
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
  font-weight: normal;
`

const LoadingHeader = styled.h1`
  color: rgb(219, 224, 255);
  font-size: 18px;
  margin-bottom: 10px;
  text-align: center;
  width: 100%;
  font-weight: normal;
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
  background-color: ${props => props.disabled ? 'rgb(88, 109, 135, 0.7)' : 'rgb(88, 109, 135)'};
  color: rgb(218, 227, 241);
  font-size: 16px;
  cursor: ${props => props.disabled ? 'not-allowed' : 'pointer'};
  transition: all 0.2s;
  position: relative;
  overflow: hidden;

  &:hover {
    background-color: ${props => props.disabled ? 'rgb(88, 109, 135, 0.7)' : '#678'};
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

const AdvancedContent = styled.div`
  margin-top: 15px;
  padding: 15px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  display: ${props => props.isExpanded ? 'block' : 'none'};
  animation: ${props => props.isExpanded ? 'slideDown 0.3s ease' : 'none'};

  @keyframes slideDown {
    from {
      opacity: 0;
      transform: translateY(-10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
`;

const CheckboxContainer = styled.div`
  display: flex;
  align-items: center;
  gap: 10px;
  color: #99aabb;
  font-size: 14px;

  input[type="checkbox"] {
    width: 14px;
    height: 14px;
    cursor: pointer;
  }
    
  label {
    cursor: pointer;
    user-select: none;
  }
`;

const ExpandIcon = () => (
  <svg width="34" height="50" viewBox="0 0 34 50" xmlns="http://www.w3.org/2000/svg" fill="none">
    <path d="M20 10 L10 25 L20 40" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
  </svg>
)

const CollapseIcon = () => (
  <svg width="34" height="50" viewBox="0 0 34 50" xmlns="http://www.w3.org/2000/svg" fill="none">
    <path d="M14 10 L24 25 L14 40" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
  </svg>
)

const RemoveIcon = () => (
  <svg width="50" height="50" viewBox="0 0 50 50" xmlns="http://www.w3.org/2000/svg" fill="none">
    <path d="M10 10 L40 40" stroke="currentColor" stroke-width="4" stroke-linecap="round"/>
    <path d="M40 10 L10 40" stroke="currentColor" stroke-width="4" stroke-linecap="round"/>
  </svg>
)

const EmptyPoster = () => (
  <svg width="200" height="300" viewBox="0 0 200 300" xmlns="http://www.w3.org/2000/svg" fill="none">
    <rect width="200" height="300" rx="10" ry="10" fill="#d3d3d3" stroke="#888" stroke-width="2"/>
    <line x1="20" y1="20" x2="180" y2="280" stroke="#888" stroke-width="2" stroke-dasharray="5,5"/>
    <line x1="180" y1="20" x2="20" y2="280" stroke="#888" stroke-width="2" stroke-dasharray="5,5"/>
    <text x="50%" y="50%" font-size="20" fill="#555" text-anchor="middle" alignment-baseline="middle">Img Not Found</text>
  </svg>
)

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

  .empty-message {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: rgb(219, 224, 255);
    font-size: 16px;
    text-align: center;
    opacity: 0.7;
    padding: 0 20px;
  }

  .toggle-button {
    position: absolute;
    left: -44px;
    top: 50%;
    transform: translateY(-50%);
    background: rgba(255, 255, 255, 0.1);
    border: none;
    color: rgb(219, 224, 255);
    padding-top: 30px;
    padding-bottom: 30px;
    cursor: pointer;
    border-radius: 4px 0 0 4px;
    backdrop-filter: blur(10px);
    display: flex;
    align-items: center;
    justify-content: center;
    width: 44px;
    height: 50px;
    
    &:hover {
      background: rgba(255, 255, 255, 0.2);
    }

    svg {
      width: 34px;
      height: 50px;
    }
  }

  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;

    h2 {
      color: rgb(219, 224, 255);
      font-size: 18px;
      font-weight: normal;
      margin: 0;
    }

    .clear-button {
      background: rgba(129, 3, 3, 0.2);
      border: none;
      color: rgb(219, 224, 255);
      cursor: pointer;
      font-size: 14px;
      padding: 4px 8px;
      border-radius: 4px;
      opacity: 0.7;
      transition: all 0.2s;

      &:hover {
        opacity: 1;
        background: rgba(129, 3, 3, 0.4);
      }
    }
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

    .movie-link {
      display: flex;
      align-items: center;
      gap: 10px;
      flex: 1;
      text-decoration: none;
      color: inherit;
      
      &:hover {
        opacity: 0.8;
      }
    }

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
      color:rgb(167, 16, 38);
      cursor: pointer;
      padding: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      opacity: 0.7;
      z-index: 2;
      width: 24px;
      height: 24px;
      
      &:hover {
        opacity: 1;
      }

      svg {
        width: 24px;
        height: 24px;
      }
    }
  }
`

const Notification = styled.div`
  position: fixed;
  top: 20px;
  right: ${props => props.isPanelExpanded ? '340px' : '20px'};
  background: rgba(129, 3, 3, 0.2);
  backdrop-filter: blur(10px);
  padding: 12px 20px;
  border-radius: 4px;
  color: rgb(219, 224, 255);
  transition: all 0.3s ease;
  opacity: ${props => props.show ? '1' : '0'};
  transform: translateY(${props => props.show ? '0' : '20px'});
  pointer-events: none;
  z-index: 1000;
`

const LoadingContainer = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  justify-content: center;
  padding: 20px;
  border-radius: 12px;
  backdrop-filter: blur(10px);
  position: relative;

  &::before {
    content: '';
    position: absolute;
    inset: -2px;
    border-radius: 14px;
    background:rgb(59, 94, 139);
    z-index: -1;
    animation: pulseBorder 2s ease-in-out infinite;
    -webkit-mask: 
      linear-gradient(#fff 0 0) content-box, 
      linear-gradient(#fff 0 0);
    -webkit-mask-composite: xor;
    mask-composite: exclude;
    padding: 2px;
  }

  @keyframes pulseBorder {
    0% {
      opacity: 0.2;
    }
    50% {
      opacity: 0.9;
    }
    100% {
      opacity: 0.2;
    }
  }

  .loading-gif {
    width: 100%;
    height: auto;
  }

  p {
    color: rgb(219, 224, 255);
    font-size: 18px;
  }
`

const ErrorContainer = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  justify-content: center;
  padding: 20px;
  border-radius: 12px;
  position: relative;
  max-width: 600px;
  width: 100%;
  margin: 40px auto;
  text-align: center;

  &::before {
    content: '';
    position: absolute;
    inset: -2px;
    border-radius: 14px;
    background: rgba(129, 3, 3, 0.2);
    z-index: -1;
    padding: 2px;
  }

  h2 {
    color: rgba(219, 224, 255, 0.8);
    font-size: 24px;
    margin: 0;
    font-weight: normal;
  }

  p {
    color: rgba(219, 224, 255, 0.8);
    font-size: 16px;
    margin: 0;
    line-height: 1.5;
  }
`

const LoadingAnimation = () => {
  const gifs = [bearGif, jarvisGif, gamblingGif];
  const gifmessage = ['Loading... please bear with us', 'Jarvis, give me some movie recs', 'May the film Gods be with you']
  let randint = Math.floor(Math.random() * gifmessage.length);
  const randomGif = gifs[randint];
  const randomMessage = gifmessage[randint];
  
  return (
    <LoadingContainer>
      <LoadingHeader>{randomMessage}</LoadingHeader>
      <img src={randomGif} alt="Loading..." className="loading-gif" />
    </LoadingContainer>
  );
};

function App() {
  const [usernames, setUsernames] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [movies, setMovies] = useState([])
  const [numMovies, setNumMovies] = useState(1)
  const [savedMovies, setSavedMovies] = useState(() => {
    const saved = localStorage.getItem('savedMovies')
    return saved ? JSON.parse(saved) : []
  })
  const [isPanelExpanded, setIsPanelExpanded] = useState(false)
  const [notification, setNotification] = useState({ message: '', show: false })
  const [isAdvancedExpanded, setIsAdvancedExpanded] = useState(false)
  const [useCache, setUseCache] = useState(true)

  useEffect(() => {
    localStorage.setItem('savedMovies', JSON.stringify(savedMovies))
  }, [savedMovies])

  const handleUsernameChange = (e) => {
    const input = e.target.value;
    const usernameList = input.split(' ').filter(u => u);
    
    if (usernameList.length > 5) {
      showNotification('Maximum 5 usernames allowed. Please try again.');
    } else {
      setError(null);
      setUsernames(input);
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setMovies([])
    try {
      const result = await getMovieRecommendations(usernames, numMovies, savedMovies.map(m => m.id), useCache)
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

  const showNotification = (message) => {
    setNotification({ message, show: true });
    setTimeout(() => {
      setNotification({ message: '', show: false });
    }, 3000);
  };

  const handleDrop = (e) => {
    e.preventDefault()
    try {
      const movie = JSON.parse(e.dataTransfer.getData('movie'))
      if (savedMovies.length >= 5) {
        showNotification('Shortlist is full (maximum 5 movies)')
      } else if (savedMovies.some(m => m.id === movie.id)) {
        showNotification('This movie is already in your shortlist')
      } else {
        setSavedMovies([...savedMovies, movie])
      }
    } catch (err) {
      console.error('Failed to add movie:', err)
    }
  }

  const removeSavedMovie = (movieId) => {
    setSavedMovies(savedMovies.filter(m => m.id !== movieId))
  }

  const clearSavedMovies = () => {
    setSavedMovies([])
  }

  return (
    <>
      <GlobalStyle />
      <Container>
        <div>
          <Logo />
          <MainContent>
            <Instructions>
              We will fetch random films from <a href="https://letterboxd.com" target="_blank" rel="noopener noreferrer">Letterboxd</a> watchlists.
              Enter up to 5 usernames separated with a space. These usernames should belong to profiles with public watchlists.
            </Instructions>

            <form onSubmit={handleSubmit}>
              <InputContainer>
                <Input
                  type="text"
                  value={usernames}
                  onChange={handleUsernameChange}
                  placeholder="ex: username1 username2 username3"
                  disabled={loading}
                />
                <SubmitButton 
                  type="submit" 
                  disabled={loading || !usernames.trim()}
                >
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

            <AdvancedOptions 
              isExpanded={isAdvancedExpanded}
              onClick={() => setIsAdvancedExpanded(!isAdvancedExpanded)}
            >
              Advanced Options
            </AdvancedOptions>

            <AdvancedContent isExpanded={isAdvancedExpanded}>
              <CheckboxContainer>
                <input
                  type="checkbox"
                  id="useCache"
                  checked={useCache}
                  onChange={(e) => setUseCache(e.target.checked)}
                />
                <label htmlFor="useCache">Use cached results</label>
              </CheckboxContainer>
            </AdvancedContent>
          </MainContent>
        </div>

        <ResultContainer>
          {loading ? (
            <LoadingAnimation />
          ) : error ? (
            <ErrorContainer>
              <h2>Something went wrong!</h2>
              <p>{error}</p>
            </ErrorContainer>
          ) : (
            <>
              {movies.length > 0 && (
                <ResultHeader>You could watch...</ResultHeader>
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
                        src={movie.image_data ? movie.image_data : EmptyPoster()}
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
            </>
          )}
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
            {isPanelExpanded ? <CollapseIcon /> : <ExpandIcon />}
          </button>
          <div className="panel-header">
            <h2>Your Shortlist ({savedMovies.length}/5)</h2>
            {savedMovies.length > 0 && (
              <button 
                className="clear-button"
                onClick={clearSavedMovies}
              >
                Clear All
              </button>
            )}
          </div>
          <div className="saved-movies-list">
            {savedMovies.length === 0 ? (
              <div className="empty-message">
                Drag movies you're interested in here
              </div>
            ) : (
              savedMovies.map(movie => (
                <div key={movie.id} className="saved-movie">
                  <a 
                    href={movie.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="movie-link"
                  >
                    {movie.image_data && (
                      <img 
                        src={movie.image_data}
                        alt={`${movie.title} poster`}
                      />
                    )}
                    <span className="title">
                      {movie.title.length > 40 ? `${movie.title.slice(0, 40)}...` : movie.title}
                    </span>
                  </a>
                  <button 
                    className="remove"
                    onClick={() => removeSavedMovie(movie.id)}
                  >
                    <RemoveIcon />
                  </button>
                </div>
              ))
            )}
          </div>
        </SavedMoviesPanel>

        <Notification 
          show={notification.show}
          isPanelExpanded={isPanelExpanded}
        >
          {notification.message}
        </Notification>
      </Container>
    </>
  )
}

export default App 
