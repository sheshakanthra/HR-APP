import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "./api";
import type {
  Department,
  EmployeeProfile,
  EmployeeSearchPage,
  LeaveBalance,
  LeaveRequest,
  LeaveType,
  OrgNode,
  Policy,
  PolicyBrief,
  PolicySearchResponse,
} from "./types";

// ---- Directory ----
export function useEmployees(search: string, departmentId: number | null, page: number) {
  const params = new URLSearchParams({ page: String(page), page_size: "25" });
  if (search) params.set("search", search);
  if (departmentId != null) params.set("department_id", String(departmentId));
  return useQuery({
    queryKey: ["employees", search, departmentId, page],
    queryFn: () => apiFetch<EmployeeSearchPage>(`/directory/employees?${params}`),
  });
}

export function useDepartments() {
  return useQuery({
    queryKey: ["departments"],
    queryFn: () => apiFetch<Department[]>("/directory/departments"),
  });
}

export function useProfile(id: number) {
  return useQuery({
    queryKey: ["profile", id],
    queryFn: () => apiFetch<EmployeeProfile>(`/directory/employees/${id}`),
  });
}

export function useOrgChart() {
  return useQuery({
    queryKey: ["org-chart"],
    queryFn: () => apiFetch<OrgNode[]>("/directory/org-chart"),
  });
}

// ---- Leave ----
export function useLeaveTypes() {
  return useQuery({
    queryKey: ["leave-types"],
    queryFn: () => apiFetch<LeaveType[]>("/leave/types"),
  });
}

export function useMyBalance() {
  return useQuery({
    queryKey: ["leave-balance"],
    queryFn: () => apiFetch<LeaveBalance[]>("/leave/balance"),
  });
}

export function useMyRequests() {
  return useQuery({
    queryKey: ["leave-requests"],
    queryFn: () => apiFetch<LeaveRequest[]>("/leave/requests"),
  });
}

export function useSubmitLeave() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: {
      leave_type_id: number;
      start_date: string;
      end_date: string;
      reason: string;
    }) => apiFetch<LeaveRequest>("/leave/requests", { method: "POST", body: JSON.stringify(body) }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["leave-requests"] });
      qc.invalidateQueries({ queryKey: ["leave-balance"] });
    },
  });
}

export function useCancelLeave() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) =>
      apiFetch<LeaveRequest>(`/leave/requests/${id}/cancel`, { method: "POST" }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["leave-requests"] });
      qc.invalidateQueries({ queryKey: ["leave-balance"] });
    },
  });
}

// ---- Approvals ----
export function useApprovalQueue() {
  return useQuery({
    queryKey: ["approvals"],
    queryFn: () => apiFetch<LeaveRequest[]>("/leave/approvals"),
  });
}

export function useDecideLeave() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, approve, note }: { id: number; approve: boolean; note: string }) =>
      apiFetch<LeaveRequest>(`/leave/requests/${id}/${approve ? "approve" : "reject"}`, {
        method: "POST",
        body: JSON.stringify({ note }),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["approvals"] }),
  });
}

// ---- Policies ----
export function usePolicies() {
  return useQuery({
    queryKey: ["policies"],
    queryFn: () => apiFetch<PolicyBrief[]>("/policies"),
  });
}

export function usePolicy(id: number | null) {
  return useQuery({
    queryKey: ["policy", id],
    queryFn: () => apiFetch<Policy>(`/policies/${id}`),
    enabled: id != null,
  });
}

export function usePolicySearch() {
  return useMutation({
    mutationFn: (q: string) =>
      apiFetch<PolicySearchResponse>(`/policies/search?q=${encodeURIComponent(q)}`),
  });
}

function invalidatePolicies(qc: ReturnType<typeof useQueryClient>) {
  qc.invalidateQueries({ queryKey: ["policies"] });
}

export function useCreatePolicy() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { title: string; category: string; body: string }) =>
      apiFetch<Policy>("/policies", { method: "POST", body: JSON.stringify(body) }),
    onSuccess: () => invalidatePolicies(qc),
  });
}

export function useUpdatePolicy() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...body }: { id: number; title?: string; category?: string; body?: string }) =>
      apiFetch<Policy>(`/policies/${id}`, { method: "PUT", body: JSON.stringify(body) }),
    onSuccess: (_d, v) => {
      invalidatePolicies(qc);
      qc.invalidateQueries({ queryKey: ["policy", v.id] });
    },
  });
}

export function usePolicyLifecycle(action: "publish" | "unpublish") {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => apiFetch<Policy>(`/policies/${id}/${action}`, { method: "POST" }),
    onSuccess: (_d, id) => {
      invalidatePolicies(qc);
      qc.invalidateQueries({ queryKey: ["policy", id] });
    },
  });
}

export function useDeletePolicy() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => apiFetch<void>(`/policies/${id}`, { method: "DELETE" }),
    onSuccess: () => invalidatePolicies(qc),
  });
}
