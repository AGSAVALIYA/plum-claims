'use client';

import { useState, useRef, useEffect, useCallback, useId } from 'react';

export interface SelectOption {
  value: string;
  label: string;
}

interface CustomSelectProps {
  label: string;
  options: SelectOption[];
  value: string;
  onChange: (value: string) => void;
  helperText?: string;
  error?: string;
  placeholder?: string;
  required?: boolean;
  disabled?: boolean;
  id?: string;
}

export default function CustomSelect({
  label,
  options,
  value,
  onChange,
  helperText,
  error,
  placeholder = 'Select an option…',
  required = false,
  disabled = false,
  id: propId,
}: CustomSelectProps) {
  const reactId = useId();
  const id = propId || reactId;
  const [isOpen, setIsOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const [typeAhead, setTypeAhead] = useState('');
  const typeAheadTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const containerRef = useRef<HTMLDivElement>(null);
  const listboxRef = useRef<HTMLUListElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);

  const selectedOption = options.find((o) => o.value === value);

  // Close on outside click
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Close on Escape
  useEffect(() => {
    if (!isOpen) return;
    function handleKey(e: KeyboardEvent) {
      if (e.key === 'Escape') {
        setIsOpen(false);
        buttonRef.current?.focus();
      }
    }
    document.addEventListener('keydown', handleKey);
    return () => document.removeEventListener('keydown', handleKey);
  }, [isOpen]);

  // Scroll active option into view
  useEffect(() => {
    if (!isOpen || activeIndex < 0 || !listboxRef.current) return;
    const items = listboxRef.current.querySelectorAll('[role="option"]');
    if (items[activeIndex]) {
      items[activeIndex].scrollIntoView({ block: 'nearest' });
    }
  }, [isOpen, activeIndex]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          if (!isOpen) {
            setIsOpen(true);
            setActiveIndex(0);
          } else {
            setActiveIndex((prev) => Math.min(prev + 1, options.length - 1));
          }
          break;

        case 'ArrowUp':
          e.preventDefault();
          if (!isOpen) {
            setIsOpen(true);
            setActiveIndex(options.length - 1);
          } else {
            setActiveIndex((prev) => Math.max(prev - 1, 0));
          }
          break;

        case 'Enter':
        case ' ':
          e.preventDefault();
          if (isOpen && activeIndex >= 0 && activeIndex < options.length) {
            onChange(options[activeIndex].value);
            setIsOpen(false);
            setActiveIndex(-1);
            buttonRef.current?.focus();
          } else {
            setIsOpen(!isOpen);
            if (!isOpen) setActiveIndex(0);
          }
          break;

        case 'Home':
          if (isOpen) {
            e.preventDefault();
            setActiveIndex(0);
          }
          break;

        case 'End':
          if (isOpen) {
            e.preventDefault();
            setActiveIndex(options.length - 1);
          }
          break;

        default:
          // Type-ahead: find first option starting with typed character
          if (/^[a-zA-Z0-9]$/.test(e.key)) {
            const newTypeAhead = typeAhead + e.key.toLowerCase();
            setTypeAhead(newTypeAhead);
            const matchIndex = options.findIndex((o) =>
              o.label.toLowerCase().startsWith(newTypeAhead)
            );
            if (matchIndex >= 0) {
              setActiveIndex(matchIndex);
              if (!isOpen) setIsOpen(true);
            }
            if (typeAheadTimer.current) clearTimeout(typeAheadTimer.current);
            typeAheadTimer.current = setTimeout(() => setTypeAhead(''), 800);
          }
          break;
      }
    },
    [isOpen, activeIndex, options, onChange, typeAhead]
  );

  const errorId = `${id}-error`;
  const helperId = `${id}-helper`;
  const describedBy = [error ? errorId : null, helperText ? helperId : null]
    .filter(Boolean)
    .join(' ') || undefined;

  return (
    <div ref={containerRef} className="relative">
      <label
        htmlFor={id}
        className="block text-sm font-semibold text-[var(--color-text-primary)] mb-1.5"
      >
        {label}
        {required && <span className="text-[var(--color-danger-500)] ml-0.5" aria-hidden="true">*</span>}
      </label>

      <button
        ref={buttonRef}
        id={id}
        type="button"
        role="combobox"
        aria-expanded={isOpen}
        aria-haspopup="listbox"
        aria-controls={`${id}-listbox`}
        aria-describedby={describedBy}
        aria-invalid={!!error}
        aria-required={required}
        disabled={disabled}
        onClick={() => {
          setIsOpen(!isOpen);
          if (!isOpen) setActiveIndex(options.findIndex((o) => o.value === value));
        }}
        onKeyDown={handleKeyDown}
        className={`
          w-full min-h-touch flex items-center justify-between gap-2
          rounded-lg border bg-[var(--color-surface-raised)] px-3.5 py-2.5
          text-sm text-left
          transition-[border-color,box-shadow] duration-150
          ${disabled ? 'opacity-50 cursor-not-allowed bg-[var(--color-surface-muted)]' : 'cursor-pointer'}
          ${error
            ? 'border-[var(--color-danger-500)] focus-visible:ring-[var(--color-danger-500)]'
            : 'border-[var(--color-border)] hover:border-[var(--color-border-hover)] focus-visible:ring-[var(--color-primary-500)]'
          }
          focus-visible:ring-2 focus-visible:ring-offset-1
        `}
      >
        <span className={selectedOption ? 'text-[var(--color-text-primary)]' : 'text-[var(--color-text-muted)]'}>
          {selectedOption ? selectedOption.label : placeholder}
        </span>
        <svg
          className={`w-4 h-4 text-[var(--color-text-muted)] transition-transform duration-150 shrink-0 ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <ul
          ref={listboxRef}
          id={`${id}-listbox`}
          role="listbox"
          aria-label={label}
          className="absolute z-50 mt-1 w-full max-h-60 overflow-auto rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] shadow-lg py-1"
        >
          {options.map((option, index) => {
            const isSelected = option.value === value;
            const isActive = index === activeIndex;
            return (
              <li
                key={option.value}
                id={`${id}-option-${index}`}
                role="option"
                aria-selected={isSelected}
                onClick={() => {
                  onChange(option.value);
                  setIsOpen(false);
                  setActiveIndex(-1);
                  buttonRef.current?.focus();
                }}
                onMouseEnter={() => setActiveIndex(index)}
                className={`
                  px-3.5 py-2.5 text-sm cursor-pointer truncate
                  transition-colors duration-150
                  ${isActive ? 'bg-[var(--color-primary-50)] text-[var(--color-primary-800)]' : ''}
                  ${isSelected && !isActive ? 'bg-[var(--color-primary-50)]' : ''}
                  ${!isActive && !isSelected ? 'text-[var(--color-text-primary)]' : ''}
                  hover:bg-[var(--color-primary-50)]
                `}
              >
                {option.label}
                {isSelected && (
                  <span className="sr-only">(selected)</span>
                )}
              </li>
            );
          })}
          {options.length === 0 && (
            <li className="px-3.5 py-2.5 text-sm text-[var(--color-text-muted)]">
              No options available
            </li>
          )}
        </ul>
      )}

      {helperText && !error && (
        <p id={helperId} className="mt-1.5 text-xs text-[var(--color-text-secondary)]">
          {helperText}
        </p>
      )}
      {error && (
        <p id={errorId} className="mt-1.5 text-xs text-[var(--color-danger-600)]" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
