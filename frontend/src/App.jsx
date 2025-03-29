import { useState } from 'react'
import styled from 'styled-components'
import Logo from './components/Logo'

const Container = styled.div`
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: space-between;
  background-color: #1a1d21;
  color: #99aabb;
  padding: 20px;
`

const MainContent = styled.div`
  text-align: center;
  max-width: 600px;
  width: 100%;
`

const Instructions = styled.p`
  margin-bottom: 20px;
  line-height: 1.6;

  a {
    color: #40bcf4;
    text-decoration: none;
    &:hover {
      text-decoration: underline;
    }
  }
`

const InputContainer = styled.div`
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
`

const Input = styled.input`
  flex: 1;
  padding: 12px 16px;
  border-radius: 4px;
  border: none;
  background-color: #ffffff;
  color: #333;
  font-size: 16px;

  &::placeholder {
    color: #999;
  }
`

const SubmitButton = styled.button`
  padding: 12px 24px;
  border-radius: 4px;
  border: none;
  background-color: #567;
  color: white;
  font-size: 16px;
  cursor: pointer;
  transition: background-color 0.2s;

  &:hover {
    background-color: #678;
  }
`

const AdvancedOptions = styled.button`
  background: none;
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

const Footer = styled.footer`
  color: #567;
  font-size: 14px;
  margin-top: auto;
  padding: 20px 0;
`

function App() {
  const [usernames, setUsernames] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    // TODO: Implement API call
  }

  return (
    <Container>
      <Logo />
      
      <MainContent>
        <Instructions>
          Enter up to 5 usernames belonging to public <a href="https://letterboxd.com" target="_blank" rel="noopener noreferrer">Letterboxd</a> profiles to get random films from the watchlists of those profiles.
          Add multiple usernames by separating with a space, and enter public lists.
        </Instructions>

        <form onSubmit={handleSubmit}>
          <InputContainer>
            <Input
              type="text"
              value={usernames}
              onChange={(e) => setUsernames(e.target.value)}
              placeholder="ex: username1 username2"
            />
            <SubmitButton type="submit">SUBMIT</SubmitButton>
          </InputContainer>
        </form>

        <AdvancedOptions>
          Advanced Options
        </AdvancedOptions>
      </MainContent>
    </Container>
  )
}

export default App 