import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';
import { IncidentTable } from '../components/incidents/IncidentTable';
import { mockIncidents } from '../api/mockData';

describe('Incident Management & Table', () => {
  it('renders incident table with incident IDs, location, and confidence tags', () => {
    render(<IncidentTable incidents={mockIncidents} onSelectIncident={() => {}} />);

    expect(screen.getByText('ACC-2026-10-08-001')).toBeInTheDocument();
    expect(screen.getByText('ACC-2026-10-08-002')).toBeInTheDocument();
    expect(screen.getAllByText(/Inspect/i).length).toBeGreaterThan(0);
  });

  it('renders empty state when incident list is empty', () => {
    render(<IncidentTable incidents={[]} onSelectIncident={() => {}} />);
    expect(screen.getByText(/No Incidents Found/i)).toBeInTheDocument();
  });
});
