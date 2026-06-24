"use client"

import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts'
import { mockRiskDistribution } from '@/lib/mock-data'

export function RiskDonut() {
  const data = [
    { name: 'High Risk', value: mockRiskDistribution.high, color: '#f43f5e' },
    { name: 'Suspicious', value: mockRiskDistribution.suspicious, color: '#f59e0b' },
    { name: 'Low Risk', value: mockRiskDistribution.low, color: '#3b82f6' },
    { name: 'Safe', value: mockRiskDistribution.safe, color: '#10b981' },
  ]

  return (
    <ResponsiveContainer width="100%" height="100%">
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={60}
          outerRadius={80}
          paddingAngle={5}
          dataKey="value"
          stroke="none"
        >
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.color} style={{ filter: `drop-shadow(0 0 4px ${entry.color}80)` }} />
          ))}
        </Pie>
        <Tooltip 
          contentStyle={{ 
            backgroundColor: '#12121a', 
            border: '1px solid #1e293b',
            borderRadius: '0.5rem',
            color: '#f1f5f9'
          }}
          itemStyle={{ color: '#f1f5f9' }}
        />
        <Legend verticalAlign="bottom" height={36} iconType="circle" />
      </PieChart>
    </ResponsiveContainer>
  )
}
