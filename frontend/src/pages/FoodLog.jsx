import React, { useState, useEffect } from 'react';
import { foodsAPI, mealsAPI } from '../services/api';

const FoodLog = () => {
  const [foods, setFoods] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedFoods, setSelectedFoods] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    loadFoods();
  }, []);

  const loadFoods = async () => {
    try {
      const response = await foodsAPI.getFoods(searchTerm);
      setFoods(response.data);
    } catch (error) {
      console.error('Error loading foods:', error);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    loadFoods();
  };

  const addFoodToMeal = (food) => {
    const existingIndex = selectedFoods.findIndex(f => f.id === food.id);
    if (existingIndex >= 0) {
      const updated = [...selectedFoods];
      updated[existingIndex].qty += 1;
      setSelectedFoods(updated);
    } else {
      setSelectedFoods([...selectedFoods, { ...food, qty: 1 }]);
    }
  };

  const updateQuantity = (foodId, qty) => {
    if (qty <= 0) {
      setSelectedFoods(selectedFoods.filter(f => f.id !== foodId));
    } else {
      setSelectedFoods(selectedFoods.map(f => 
        f.id === foodId ? { ...f, qty } : f
      ));
    }
  };

  const logMeal = async () => {
    if (selectedFoods.length === 0) {
      setMessage('Please add some foods to your meal');
      return;
    }

    setLoading(true);
    try {
      const items = selectedFoods.map(food => ({
        name: food.name,
        qty: food.qty
      }));

      await mealsAPI.logMeal(items);
      setMessage('Meal logged successfully!');
      setSelectedFoods([]);
    } catch (error) {
      setMessage('Error logging meal: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const totalCalories = selectedFoods.reduce((sum, food) => 
    sum + (food.cal * food.qty), 0
  );

  return (
    <div>
      <h1>Food Log</h1>
      <p className="mb-20">Log your meals and track nutrition</p>

      <div className="grid grid-2">
        {/* Food Search */}
        <div className="card">
          <h3>Search Foods</h3>
          <form onSubmit={handleSearch} className="flex gap-10" style={{ marginBottom: '20px' }}>
            <input
              type="text"
              placeholder="Search foods..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{ flex: 1 }}
            />
            <button type="submit" className="btn">Search</button>
          </form>

          <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
            {foods.map(food => (
              <div key={food.id} className="flex flex-between" style={{ 
                padding: '10px', 
                border: '1px solid #ddd', 
                borderRadius: '4px',
                marginBottom: '10px'
              }}>
                <div>
                  <strong>{food.name}</strong>
                  <p style={{ margin: '5px 0', fontSize: '14px', color: '#666' }}>
                    {food.serving_desc}
                  </p>
                  <p style={{ margin: 0, fontSize: '12px', color: '#888' }}>
                    {food.cal} cal | {food.protein}g protein | {food.carbs}g carbs | {food.fat}g fat
                  </p>
                </div>
                <button 
                  onClick={() => addFoodToMeal(food)}
                  className="btn"
                  style={{ padding: '5px 10px', fontSize: '12px' }}
                >
                  Add
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Selected Foods */}
        <div className="card">
          <h3>Current Meal</h3>
          {selectedFoods.length === 0 ? (
            <p style={{ color: '#666', textAlign: 'center', marginTop: '50px' }}>
              No foods selected. Search and add foods to log a meal.
            </p>
          ) : (
            <>
              <div style={{ maxHeight: '300px', overflowY: 'auto', marginBottom: '20px' }}>
                {selectedFoods.map(food => (
                  <div key={food.id} className="flex flex-between" style={{ 
                    padding: '10px', 
                    border: '1px solid #ddd', 
                    borderRadius: '4px',
                    marginBottom: '10px'
                  }}>
                    <div>
                      <strong>{food.name}</strong>
                      <p style={{ margin: '5px 0', fontSize: '14px', color: '#666' }}>
                        {food.cal * food.qty} cal | {food.protein * food.qty}g protein
                      </p>
                    </div>
                    <div className="flex gap-10" style={{ alignItems: 'center' }}>
                      <input
                        type="number"
                        value={food.qty}
                        onChange={(e) => updateQuantity(food.id, parseFloat(e.target.value) || 0)}
                        style={{ width: '60px', padding: '5px' }}
                        min="0"
                        step="0.1"
                      />
                      <button 
                        onClick={() => updateQuantity(food.id, 0)}
                        className="btn btn-secondary"
                        style={{ padding: '5px 10px', fontSize: '12px' }}
                      >
                        Remove
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              <div style={{ 
                padding: '15px', 
                background: '#f8f9fa', 
                borderRadius: '4px',
                marginBottom: '20px'
              }}>
                <div className="flex flex-between">
                  <strong>Total Calories:</strong>
                  <strong>{totalCalories.toFixed(0)}</strong>
                </div>
              </div>

              <button 
                onClick={logMeal}
                className="btn"
                style={{ width: '100%' }}
                disabled={loading}
              >
                {loading ? 'Logging...' : 'Log Meal'}
              </button>
            </>
          )}

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
      </div>
    </div>
  );
};

export default FoodLog;
