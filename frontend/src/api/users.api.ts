import apiClient from './client';

export interface ManagerUser {
  id: number;
  name: string;
  login: string;
}

export const usersApi = {
  getManagers: async (department_id?: number): Promise<{ success: boolean; data: ManagerUser[] }> => {
    const response = await apiClient.post('/api/users/managers', { department_id });
    return response.data;
  },
};


