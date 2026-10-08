import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';
import { MaintenanceBanner } from '../components/common/MaintenanceBanner';
import { SettingsProvider } from '../context/SettingsContext';
import { AuthProvider } from '../context/AuthContext';

describe('Maintenance Mode Safety Guards', () => {
  it('does not render banner when maintenance mode is inactive', () => {
    render(
      <AuthProvider>
        <SettingsProvider>
          <MaintenanceBanner />
        </SettingsProvider>
      </AuthProvider>
    );

    expect(screen.queryByText(/SYSTEM IN MAINTENANCE MODE/i)).toBeNull();
  });
});
