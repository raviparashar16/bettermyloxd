import styled from 'styled-components'
import logoImage from './logo.png'

const LogoContainer = styled.div`
  margin-top: 20px;
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  img {
    width: 260px;
    height: 190px;
  }
`

export default function Logo() {
  return (
    <LogoContainer>
      <img src={logoImage} alt="BetterMyLoxd Logo" />
    </LogoContainer>
  )
} 