import React, { InputHTMLAttributes } from 'react';

interface CheckboxProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'onChange'> {
  label: string;
  helperText?: string;
  error?: string;
  checked?: boolean;
  onChange?: (checked: boolean) => void;
}

const Checkbox: React.FC<CheckboxProps> = ({
  label,
  helperText,
  error,
  checked = false,
  onChange,
  className = '',
  id,
  ...rest
}) => {
  const checkboxId = id || `checkbox-${Math.random().toString(36).substring(2, 9)}`;

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (onChange) {
      onChange(e.target.checked);
    }
  };

  return (
    <div className="mb-4">
      <div className="flex items-start">
        <div className="flex items-center h-5">
          <input
            id={checkboxId}
            type="checkbox"
            checked={checked}
            onChange={handleChange}
            className={`
              h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500
              ${error ? 'border-red-300 text-red-600 focus:ring-red-500' : ''}
              ${className}
            `}
            aria-invalid={!!error}
            aria-describedby={
              helperText ? `${checkboxId}-helper-text` : error ? `${checkboxId}-error` : undefined
            }
            {...rest}
          />
        </div>
        <div className="ml-3 text-sm">
          <label
            htmlFor={checkboxId}
            className={`font-medium ${error ? 'text-red-600' : 'text-gray-700'}`}
          >
            {label}
          </label>
          {helperText && !error && (
            <p
              id={`${checkboxId}-helper-text`}
              className="text-gray-500"
            >
              {helperText}
            </p>
          )}
          {error && (
            <p
              id={`${checkboxId}-error`}
              className="text-red-600"
              role="alert"
            >
              {error}
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

export default Checkbox;