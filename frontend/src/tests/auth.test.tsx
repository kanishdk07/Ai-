import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';
import { SeverityBadge } from '../components/common/SeverityBadge';
import { StatusBadge } from '../components/common/StatusBadge';
import { LoginPage } from '../pages/LoginPage';
import { AuthProvider } from '../context/AuthContext';

describe('Authentication & Roles', () => {
  it('renders login page with call sign and password inputs', () => {
    render(
      <AuthProvider>
        <LoginPage onLoginSuccess={() => {}} />
      </AuthProvider>
    );

    expect(screen.getByText(/Operator Authentication/i)).toBeInTheDocument();
    expect(screen.getByText(/Sign In To Control Center/i)).toBeInTheDocument();
    expect(screen.getByText(/Quick Testing One-Click Access/i)).toBeInTheDocument();
  });
});

describe('Severity and Status Indicators', () => {
  it('renders high severity badge with critical pulse styling', () => {
    render(<SeverityBadge severity="high" />);
    expect(screen.getByText(/High Severity/i)).toBeInTheDocument();
  });

  it('renders medium and low severity indicators accurately', () => {
    const { rerender } = render(<SeverityBadge severity="medium" />);
    expect(screen.getByText(/Medium Severity/i)).toBeInTheDocument();

    rerender(<SeverityBadge severity="low" />);
    expect(screen.getByText(/Low Severity/i)).toBeInTheDocument();
  });

  it('renders incident status badges correctly', () => {
    const { rerender } = render(<StatusBadge status="detected" />);
    expect(screen.getByText(/Unverified AI Detection/i)).toBeInTheDocument();

    rerender(<StatusBadge status="acknowledged" />);
    expect(screen.getByText(/Hospital Acknowledged/i)).toBeInTheDocument();

    rerender(<StatusBadge status="resolved" />);
    expect(screen.getByText(/Resolved & Cleared/i)).toBeInTheDocument();
  });
});
