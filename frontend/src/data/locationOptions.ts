export const COUNTRIES = ['South Africa'];

export const PROVINCES_BY_COUNTRY: Record<string, string[]> = {
  'South Africa': [
    'Western Cape',
    'Gauteng',
    'KwaZulu-Natal',
    'Eastern Cape',
    'Free State',
    'Limpopo',
    'Mpumalanga',
    'North West',
    'Northern Cape',
  ],
};

export const CITIES_BY_PROVINCE: Record<string, string[]> = {
  'Western Cape': ['Cape Town', 'Stellenbosch', 'Paarl', 'George', 'Worcester'],
  Gauteng: ['Johannesburg', 'Pretoria', 'Midrand', 'Centurion'],
  'KwaZulu-Natal': ['Durban', 'Pietermaritzburg', 'Richards Bay'],
  'Eastern Cape': ['Gqeberha', 'East London', 'Mthatha'],
  'Free State': ['Bloemfontein', 'Welkom'],
  Limpopo: ['Polokwane', 'Tzaneen'],
  Mpumalanga: ['Nelspruit', 'Witbank'],
  'North West': ['Rustenburg', 'Mahikeng'],
  'Northern Cape': ['Kimberley', 'Upington'],
};
