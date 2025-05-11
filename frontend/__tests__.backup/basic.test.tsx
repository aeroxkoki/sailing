import React from 'react'
import { render } from '@testing-library/react'

// 基本的なテスト
describe('Basic test', () => {
  it('should pass', () => {
    expect(true).toBe(true)
  })

  it('should render a basic component', () => {
    const TestComponent = () => <div>Hello, Test\!</div>
    const { getByText } = render(<TestComponent />)
    expect(getByText('Hello, Test\!')).toBeInTheDocument()
  })
})
