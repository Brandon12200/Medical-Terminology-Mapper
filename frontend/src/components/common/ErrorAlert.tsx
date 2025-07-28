interface ErrorAlertProps {
  message: string;
}

export const ErrorAlert = ({ message }: ErrorAlertProps) => {
  return (
    <div className="error-container">
      <span>⚠️</span>
      <div>
        <strong>Error:</strong> {message}
      </div>
    </div>
  );
};