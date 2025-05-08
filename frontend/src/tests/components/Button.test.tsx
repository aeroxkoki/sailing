import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import Button from '@/components/common/Button';

describe('Button component', () => {
  it('renders correctly with default props', () => {
    render(<Button>Test Button</Button>);
    const button = screen.getByText('Test Button');
    expect(button).toBeInTheDocument();
    expect(button).toHaveClass('bg-blue-600'); // デフォルトのprimaryボタンのクラス
  });

  it('renders with secondary variant', () => {
    render(<Button variant="secondary">Secondary Button</Button>);
    const button = screen.getByText('Secondary Button');
    expect(button).toHaveClass('bg-gray-600');
  });

  it('renders with outline variant', () => {
    render(<Button variant="outline">Outline Button</Button>);
    const button = screen.getByText('Outline Button');
    expect(button).toHaveClass('border-blue-600');
    expect(button).toHaveClass('text-blue-600');
  });

  it('renders with ghost variant', () => {
    render(<Button variant="ghost">Ghost Button</Button>);
    const button = screen.getByText('Ghost Button');
    expect(button).toHaveClass('text-gray-300');
  });

  it('handles click events', () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Clickable Button</Button>);
    const button = screen.getByText('Clickable Button');
    fireEvent.click(button);
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('displays loading state correctly', () => {
    render(<Button isLoading>Loading Button</Button>);
    expect(screen.getByText('Loading Button')).toBeInTheDocument();
    expect(screen.getByRole('status')).toBeInTheDocument(); // LoadingSpinnerのrole
  });

  it('can be disabled', () => {
    render(<Button disabled>Disabled Button</Button>);
    const button = screen.getByText('Disabled Button');
    expect(button).toBeDisabled();
  });

  it('renders with full width', () => {
    render(<Button fullWidth>Full Width Button</Button>);
    const button = screen.getByText('Full Width Button');
    expect(button).toHaveClass('w-full');
  });

  it('renders with icon', () => {
    const icon = <svg data-testid="test-icon"></svg>;
    render(<Button icon={icon}>Button with Icon</Button>);
    expect(screen.getByTestId('test-icon')).toBeInTheDocument();
  });
});
