import { ArrowRight, Search, X } from "lucide-react";
import type { FormEvent } from "react";
import { Button } from "@/components/ui/button";

type DestinationSearchProps = {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  onClear: () => void;
  onNavigateResults?: () => void;
};

export function DestinationSearch({ value, onChange, onSubmit, onClear, onNavigateResults }: DestinationSearchProps) {
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onSubmit();
  }

  return (
    <form className="destination-search" onSubmit={submit} role="search">
      <Search size={21} aria-hidden="true" />
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder="Para onde você quer ir?"
        aria-label="Buscar destino, linha ou ponto"
        aria-controls="destination-suggestions"
        onKeyDown={(event) => {
          if (event.key === "ArrowDown" && onNavigateResults) {
            event.preventDefault();
            onNavigateResults();
          }
        }}
        autoComplete="off"
      />
      {value && (
        <Button variant="ghost" size="sm" onClick={onClear} aria-label="Limpar busca" title="Limpar busca">
          <X size={17} />
        </Button>
      )}
      <Button variant="icon" type="submit" aria-label="Buscar" title="Buscar">
        <ArrowRight size={19} />
      </Button>
    </form>
  );
}
