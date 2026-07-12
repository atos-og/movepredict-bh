import { ChevronRight, Search } from "lucide-react";
import type { FormEvent } from "react";
import { Button } from "@/components/ui/button";

type SearchFieldProps = {
  value: string;
  placeholder: string;
  label: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
};

export function SearchField({
  value,
  placeholder,
  label,
  onChange,
  onSubmit,
}: SearchFieldProps) {
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onSubmit();
  }

  return (
    <form className="search-form" onSubmit={submit} role="search">
      <Search size={18} aria-hidden="true" />
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        aria-label={label}
      />
      <Button variant="icon" size="sm" type="submit" aria-label="Buscar" title="Buscar">
        <ChevronRight size={19} />
      </Button>
    </form>
  );
}
