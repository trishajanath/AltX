import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs) {
  return twMerge(clsx(inputs));
}

// Export twMerge directly for backward compatibility
export { twMerge };

export const buttonVariants = {
  default: "bg-blue-600 text-white hover:bg-blue-700",
  outline: "border border-gray-300 bg-white text-gray-900 hover:bg-gray-50",
  ghost: "text-gray-900 hover:bg-gray-100",
  destructive: "bg-red-600 text-white hover:bg-red-700"
};

export const cardVariants = {
  default: "rounded-lg border bg-white p-6 shadow-sm",
  elevated: "rounded-lg border bg-white p-6 shadow-lg"
};
