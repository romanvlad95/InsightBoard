import { rest } from 'msw'

const API_URL = 'http://localhost:8000/api/v1'

export const handlers = [
  // Auth endpoints
  rest.post(`${API_URL}/auth/register`, (req, res, ctx) => {
    return res(
      ctx.status(201),
      ctx.json({
        id: 1,
        email: 'test@example.com',
        role: 'user',
      })
    )
  }),

  rest.post(`${API_URL}/auth/login`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        access_token: 'mock-jwt-token',
        token_type: 'bearer',
      })
    )
  }),

  // Dashboards endpoints
  rest.get(`${API_URL}/dashboards`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json([
        {
          id: 1,
          name: 'Test Dashboard',
          description: 'Test description',
          owner_id: 1,
          created_at: '2025-10-22T00:00:00Z',
        },
      ])
    )
  }),

  rest.get(`${API_URL}/dashboards/1/metrics`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json([
        {
          id: 1,
          name: 'cpu_usage',
          value: 75.5,
          metric_type: 'gauge',
          dashboard_id: 1,
          created_at: '2025-10-22T00:00:00Z',
        },
      ])
    )
  }),
]
