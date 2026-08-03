import axios from 'axios'

// 统一指向本地后端的 8001 端口
const API_BASE_URL = '/api'

export function getCurrentAccount() {
  const account = localStorage.getItem('currentAccount')
  return account ? JSON.parse(account) : null
}

export function setCurrrentAccount(accountData) {
  localStorage.setItem('currentAccount', JSON.stringify(accountData))
}

export function clearCurrentAccount() {
  localStorage.removeItem('currentAccount')
}

export const api = {
  // 1. 登录
  async login(login_name, password) {
    try {
      const response = await axios.post(`${API_BASE_URL}/login`, { login_name, password })
      if (response.data && response.data.account_id) {
        setCurrrentAccount(response.data)
        return { data: response.data, error: null }
      }
      return { data: null, error: { message: '登录响应异常' } }
    } catch (err) {
      return { 
        data: null, 
        error: { message: err.response?.data?.detail || '服务器连接失败' } 
      }
    }
  },

  // 2. 注册
  async register(login_name, password, display_name, birthday) {
    try {
      const response = await axios.post(`${API_BASE_URL}/register`, { 
        login_name, 
        password, 
        display_name, 
        birthday 
      })
      if (response.data && response.data.account_id) {
        setCurrrentAccount(response.data)
        return { data: response.data, error: null }
      }
      return { data: null, error: { message: '注册响应异常' } }
    } catch (err) {
      return { 
        data: null, 
        error: { message: err.response?.data?.detail || '服务器连接失败' } 
      }
    }
  },

  // ⬇️ 这里保留你之前写的 getRecords, addRecord, deleteRecord 等方法 ⬇️
  // ... [保留你原有的业务代码] ...
}