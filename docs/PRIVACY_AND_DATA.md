# Privacidade, fonte e retencao

## Dados tratados

O backend armazena dados operacionais de transporte: identificador publico do veiculo, linha,
viagem inferida, coordenadas, velocidade, sentido e horario. O projeto nao precisa armazenar conta,
nome, telefone nem historico de localizacao do usuario.

A geolocalizacao do passageiro e solicitada pelo navegador e usada no frontend para contexto e
busca de pontos proximos. Ela nao deve ser enviada ao backend ou persistida sem uma decisao futura,
consentimento explicito e atualizacao deste documento.

## Fonte e atribuicao

- GTFS e posicoes: Portal de Dados Abertos da Prefeitura de Belo Horizonte.
- O portal declara a fonte TRANSFACIL / Superintendencia de Mobilidade da PBH.
- A documentacao da fonte declara Creative Commons Attribution.
- A demonstracao deve manter atribuicao visivel a PBH e nao sugerir que a previsao e oficial.

Antes de producao, a equipe deve reler os termos vigentes da fonte e registrar data e link da
revisao. Esta avaliacao tecnica nao substitui aconselhamento juridico.

## Retencao

- posicoes historicas: 90 dias por padrao;
- exclusao: lotes de 50 mil pelo worker de retencao;
- previsoes e chegadas: manter somente pelo periodo necessario para avaliacao e case study;
- backups devem seguir o mesmo prazo ou possuir expiracao documentada;
- logs nao devem conter cookies, tokens, URLs com credenciais ou localizacao de passageiros.

## Acesso e incidente

- banco e paineis acessiveis somente a Atos e Vinicius durante staging;
- secrets apenas no provedor e GitHub Environment autorizado;
- suspeita de vazamento exige rotacao do segredo, preservacao de logs operacionais e retirada
  temporaria do ambiente publico;
- dados exportados para avaliacao devem remover qualquer campo nao necessario.
