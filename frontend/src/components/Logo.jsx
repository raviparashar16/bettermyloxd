import styled from 'styled-components'
import logoImage from './logo.png'

const LogoContainer = styled.div`
  margin: 40px 0;
  img {
    width: 200px;
    height: 200px;
  }
`

export default function Logo() {
  return (
    <LogoContainer>
      <img src={logoImage} alt="BetterMyLoxd Logo" />
    </LogoContainer>
  )
} 