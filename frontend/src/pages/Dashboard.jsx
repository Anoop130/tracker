import React, { useState, useEffect } from 'react';
import { nutritionAPI } from '../services/api';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import { Doughnut } from 'react-chartjs-2';

ChartJS.register(ArcElement, Tooltip, Legend);

const Dashboard = () => {
  const [summary, setSummary] = useState(null);
  const [goals, setGoals] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [summaryData, goalsData] = await Promise.all([
        nutritionAPI.getSummary(),
        nutritionAPI.getGoals()
      ]);
      
      setSummary(summaryData.data);
      setGoals(goalsData.data);
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="text-center">Loading dashboard...</div>;
  }

  const macroData = {
    labels: ['Protein', 'Carbs', 'Fat'],
    datasets: [{
      data: [
        summary?.protein || 0,
        summary?.carbs || 0,
        summary?.fat || 0
      ],
      backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56'],
      borderWidth: 0
    }]
  };

  const macroOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'bottom'
      }
    }
  };

  const getProgressPercentage = (current, goal) => {
    if (!goal || goal === 0) return 0;
    return Math.min((current / goal) * 100, 100);
  };

  return (
    <div>
      <h1>Nutrition Dashboard</h1>
      <p className="mb-20">Track your daily nutrition progress</p>

      <div className="grid grid-2">
        {/* Daily Summary */}
        <div className="card">
          <h3>Today's Intake</h3>
          <div className="grid grid-2" style={{ marginTop: '20px' }}>
            <div className="text-center">
              <h4 style={{ color: '#FF6384' }}>{summary?.cal?.toFixed(0) || 0}</h4>
              <p>Calories</p>
            </div>
            <div className="text-center">
              <h4 style={{ color: '#36A2EB' }}>{summary?.protein?.toFixed(0) || 0}g</h4>
              <p>Protein</p>
            </div>
            <div className="text-center">
              <h4 style={{ color: '#FFCE56' }}>{summary?.carbs?.toFixed(0) || 0}g</h4>
              <p>Carbs</p>
            </div>
            <div className="text-center">
              <h4 style={{ color: '#4BC0C0' }}>{summary?.fat?.toFixed(0) || 0}g</h4>
              <p>Fat</p>
            </div>
          </div>
        </div>

        {/* Macro Breakdown Chart */}
        <div className="card">
          <h3>Macro Breakdown</h3>
          <div style={{ height: '300px', marginTop: '20px' }}>
            <Doughnut data={macroData} options={macroOptions} />
          </div>
        </div>
      </div>

      {/* Goals Progress */}
      {goals && (
        <div className="card">
          <h3>Goal Progress</h3>
          <div className="grid grid-2" style={{ marginTop: '20px' }}>
            <div>
              <div className="flex flex-between">
                <span>Calories</span>
                <span>{summary?.cal?.toFixed(0) || 0} / {goals.calories}</span>
              </div>
              <div style={{ 
                width: '100%', 
                height: '8px', 
                background: '#e9ecef', 
                borderRadius: '4px',
                marginTop: '5px'
              }}>
                <div style={{
                  width: `${getProgressPercentage(summary?.cal, goals.calories)}%`,
                  height: '100%',
                  background: '#007bff',
                  borderRadius: '4px'
                }}></div>
              </div>
            </div>

            <div>
              <div className="flex flex-between">
                <span>Protein</span>
                <span>{summary?.protein?.toFixed(0) || 0}g / {goals.protein_g}g</span>
              </div>
              <div style={{ 
                width: '100%', 
                height: '8px', 
                background: '#e9ecef', 
                borderRadius: '4px',
                marginTop: '5px'
              }}>
                <div style={{
                  width: `${getProgressPercentage(summary?.protein, goals.protein_g)}%`,
                  height: '100%',
                  background: '#FF6384',
                  borderRadius: '4px'
                }}></div>
              </div>
            </div>

            <div>
              <div className="flex flex-between">
                <span>Carbs</span>
                <span>{summary?.carbs?.toFixed(0) || 0}g / {goals.carbs_g}g</span>
              </div>
              <div style={{ 
                width: '100%', 
                height: '8px', 
                background: '#e9ecef', 
                borderRadius: '4px',
                marginTop: '5px'
              }}>
                <div style={{
                  width: `${getProgressPercentage(summary?.carbs, goals.carbs_g)}%`,
                  height: '100%',
                  background: '#36A2EB',
                  borderRadius: '4px'
                }}></div>
              </div>
            </div>

            <div>
              <div className="flex flex-between">
                <span>Fat</span>
                <span>{summary?.fat?.toFixed(0) || 0}g / {goals.fat_g}g</span>
              </div>
              <div style={{ 
                width: '100%', 
                height: '8px', 
                background: '#e9ecef', 
                borderRadius: '4px',
                marginTop: '5px'
              }}>
                <div style={{
                  width: `${getProgressPercentage(summary?.fat, goals.fat_g)}%`,
                  height: '100%',
                  background: '#FFCE56',
                  borderRadius: '4px'
                }}></div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="card">
        <h3>Quick Actions</h3>
        <div className="flex gap-20" style={{ marginTop: '20px' }}>
          <a href="/food-log" className="btn">Log Food</a>
          <a href="/goals" className="btn btn-secondary">Set Goals</a>
          <a href="/chat" className="btn btn-secondary">Chat with Coach</a>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
