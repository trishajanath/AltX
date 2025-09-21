```typescript
import React from 'react';
import { AlertTriangle } from 'lucide-react';

interface ErrorMessageProps {
  message: string;
}

const ErrorMessage: React.FC = ({ message }) => {
  return (

          Error
          {message}

  );
};

export default ErrorMessage;
```