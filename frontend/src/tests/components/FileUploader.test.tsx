import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import FileUploader from '@/components/upload/FileUploader';

describe('FileUploader component', () => {
  const mockOnFileSelect = jest.fn();
  const defaultProps = {
    onFileSelect: mockOnFileSelect,
    acceptedFileTypes: '.gpx,.csv,.fit,.tcx',
    maxSize: 10, // MB
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders correctly', () => {
    render(<FileUploader {...defaultProps} />);
    expect(screen.getByText(/GPSログをアップロード/i)).toBeInTheDocument();
    expect(screen.getByText(/ドラッグ＆ドロップまたはクリック/i)).toBeInTheDocument();
  });

  it('accepts valid file when clicked', async () => {
    render(<FileUploader {...defaultProps} />);
    
    const file = new File(['gps data content'], 'track.gpx', { type: 'application/gpx+xml' });
    const input = screen.getByRole('textbox', { hidden: true }); // 非表示のinput要素を取得
    
    // ファイル選択をシミュレート
    await userEvent.upload(input, file);
    
    expect(mockOnFileSelect).toHaveBeenCalledWith(file);
    expect(mockOnFileSelect).toHaveBeenCalledTimes(1);
  });

  it('shows error for invalid file type', async () => {
    render(<FileUploader {...defaultProps} />);
    
    const file = new File(['invalid file content'], 'document.pdf', { type: 'application/pdf' });
    const input = screen.getByRole('textbox', { hidden: true });
    
    // ファイル選択をシミュレート
    await userEvent.upload(input, file);
    
    expect(mockOnFileSelect).not.toHaveBeenCalled();
    expect(screen.getByText(/対応していないファイル形式です/i)).toBeInTheDocument();
  });

  it('shows error for oversized file', async () => {
    render(<FileUploader {...defaultProps} />);
    
    // ファイルサイズのモック（10MBを超えるサイズ）
    const file = new File([''], 'large.gpx', { type: 'application/gpx+xml' });
    Object.defineProperty(file, 'size', { value: 11 * 1024 * 1024 }); // 11MB
    
    const input = screen.getByRole('textbox', { hidden: true });
    
    // ファイル選択をシミュレート
    await userEvent.upload(input, file);
    
    expect(mockOnFileSelect).not.toHaveBeenCalled();
    expect(screen.getByText(/ファイルサイズが大きすぎます/i)).toBeInTheDocument();
  });

  it('handles drag and drop', () => {
    render(<FileUploader {...defaultProps} />);
    const dropzone = screen.getByText(/GPSログをアップロード/i).closest('div');
    
    // ドラッグイベントのシミュレート
    fireEvent.dragOver(dropzone);
    expect(dropzone).toHaveClass('border-blue-500');
    
    fireEvent.dragLeave(dropzone);
    expect(dropzone).not.toHaveClass('border-blue-500');
  });
});
