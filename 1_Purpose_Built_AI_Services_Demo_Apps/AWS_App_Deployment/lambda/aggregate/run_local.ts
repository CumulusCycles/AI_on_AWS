import app from './index';

const PORT = process.env.PORT || 8001;

app.listen(PORT, () => {
  console.log(`Aggregate Lambda running on http://localhost:${PORT}`);
  console.log(`Health check: http://localhost:${PORT}/health`);
});