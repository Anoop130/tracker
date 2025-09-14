import React, { useState, useEffect } from 'react';
import { nutritionAPI } from '../services/api';

const Goals = () => {
  const [goals, setGoals] = useState({
    calories: 2000,
    protein_g: 150,
    carbs_g: 200,
    fat_g: 80
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    loadGoals();
  }, []);

  const loadGoals = async () => {
    try {
      const response = await nutritionAPI.getGoals();
      setGoals(response.data);
    } catch (error) {
      console.error('Error loading goals:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');

    try {
      await nutritionAPI.setGoals(goals);
      setMessage('Goals updated successfully!');
    } catch (error) {
      setMessage('Error updating goals: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (field, value) => {
    setGoals(prev => ({
      ...prev,
      [field]: parseFloat(value) || 0
    }));
  };

  return (
    <div>
      <h1>Nutrition Goals</h1>
      <p className="mb-20">Set your daily nutrition targets</p>

      <div className="grid grid-2">
        <div className="card">
          <h3>Set Goals</h3>
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label>Daily Calories</label>
              <input
                type="number"
                value={goals.calories}
                onChange={(e) => handleChange('calories', e.target.value)}
                min="0"
                step="10"
              />
            </div>

            <div className="form-group">
              <label>Protein (grams)</label>
              <input
                type="number"
                value={goals.protein_g}
                onChange={(e) => handleChange('protein_g', e.target.value)}
                min="0"
                step="1"
              />
            </div>

            <div className="form-group">
              <label>Carbohydrates (grams)</label>
              <input
                type="number"
                value={goals.carbs_g}
                onChange={(e) => handleChange('carbs_g', e.target.value)}
                min="0"
                step="1"
              />
            </div>

            <div className="form-group">
              <label>Fat (grams)</label>
              <input
                type="number"
                value={goals.fat_g}
                onChange={(e) => handleChange('fat_g', e.target.value)}
                min="0"
                step="1"
              />
            </div>

            <button 
              type="submit" 
              className="btn"
              disabled={loading}
            >
              {loading ? 'Updating...' : 'Update Goals'}
            </button>
          </form>

          {message && (
            <div style={{ 
              marginTop: '15px', 
              padding: '10px', 
              background: message.includes('Error') ? '#f8d7da' : '#d4edda',
              color: message.includes('Error') ? '#721c24' : '#155724',
              borderRadius: '4px'
            }}>
              {message}
            </div>
          )}
        </div>

        <div className="card">
          <h3>Goal Guidelines</h3>
          <div style={{ fontSize: '14px', lineHeight: '1.6' }}>
            <h4>Calorie Targets:</h4>
            <ul style={{ marginBottom: '20px' }}>
              <li><strong>Weight Loss:</strong> 500-1000 cal deficit per day</li>
              <li><strong>Weight Maintenance:</strong> Current weight × 15-17</li>
              <li><strong>Weight Gain:</strong> 300-500 cal surplus per day</li>
            </ul>

            <h4>Macro Guidelines:</h4>
            <ul style={{ marginBottom: '20px' }}>
              <li><strong>Protein:</strong> 1.6-2.2g per kg body weight</li>
              <li><strong>Fat:</strong> 20-30% of total calories</li>
              <li><strong>Carbs:</strong> Remaining calories after protein & fat</li>
            </ul>

            <h4>Quick Presets:</h4>
            <div className="flex gap-10" style={{ marginTop: '10px' }}>
              <button 
                type="button"
                onClick={() => setGoals({
                  calories: 1500,
                  protein_g: 120,
                  carbs_g: 150,
                  fat_g: 60
                })}
                className="btn btn-secondary"
                style={{ fontSize: '12px', padding: '5px 10px' }}
              >
                Weight Loss
              </button>
              <button 
                type="button"
                onClick={() => setGoals({
                  calories: 2000,
                  protein_g: 150,
                  carbs_g: 200,
                  fat_g: 80
                })}
                className="btn btn-secondary"
                style={{ fontSize: '12px', padding: '5px 10px' }}
              >
                Maintenance
              </button>
              <button 
                type="button"
                onClick={() => setGoals({
                  calories: 2500,
                  protein_g: 180,
                  carbs_g: 250,
                  fat_g: 100
                })}
                className="btn btn-secondary"
                style={{ fontSize: '12px', padding: '5px 10px' }}
              >
                Weight Gain
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Goals;
