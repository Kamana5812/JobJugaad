import { api, apiUrl } from './client'

export async function getHealth(signal) {
  if (!apiUrl) {
    throw new Error('The backend address has not been configured yet.')
  }

  const { data } = await api.get('/health', { signal })
  if (
    data.status !== 'ok' ||
    data.service !== 'jobjugaad-api' ||
    !['connected', 'not_configured'].includes(data.database)
  ) {
    throw new Error('The backend returned an unexpected health response.')
  }
  return data
}
