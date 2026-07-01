export type RBACRole = "employee" | "manager" | "hr_admin" | "super_admin";
export type LeaveStatus = "pending" | "approved" | "rejected" | "cancelled";

export interface UserOut {
  id: number;
  email: string;
  rbac_role: RBACRole;
  is_active: boolean;
  employee_id: number | null;
}

export interface EmployeeBrief {
  id: number;
  first_name: string;
  last_name: string;
  work_email: string;
  title: string;
  department_id: number | null;
  manager_id: number | null;
}

export interface MeOut {
  user: UserOut;
  employee: EmployeeBrief | null;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: UserOut;
}

export interface EmployeeCard {
  id: number;
  first_name: string;
  last_name: string;
  work_email: string;
  title: string;
  department_id: number | null;
  department_name: string | null;
  manager_id: number | null;
}

export interface ManagerRef {
  id: number;
  first_name: string;
  last_name: string;
  title: string;
  work_email: string;
}

export interface EmployeeProfile extends EmployeeCard {
  location: string;
  hire_date: string;
  employment_status: string;
  manager: ManagerRef | null;
  direct_reports: EmployeeCard[];
}

export interface EmployeeSearchPage {
  items: EmployeeCard[];
  total: number;
  page: number;
  page_size: number;
}

export interface OrgNode {
  id: number;
  first_name: string;
  last_name: string;
  title: string;
  department_name: string | null;
  reports: OrgNode[];
}

export interface Department {
  id: number;
  name: string;
}

export interface LeaveType {
  id: number;
  name: string;
  code: string;
  annual_accrual_days: number;
  description: string;
}

export interface LeaveBalance {
  leave_type_id: number;
  leave_type_name: string;
  leave_type_code: string;
  accrued: number;
  used: number;
  available: number;
}

export interface LeaveRequest {
  id: number;
  employee_id: number;
  leave_type_id: number;
  leave_type_name: string | null;
  start_date: string;
  end_date: string;
  days: number;
  reason: string;
  status: LeaveStatus;
  approver_id: number | null;
  decided_at: string | null;
  decision_note: string;
  created_via_agent: boolean;
  created_at: string;
  employee: {
    id: number;
    first_name: string;
    last_name: string;
    work_email: string;
  } | null;
}
