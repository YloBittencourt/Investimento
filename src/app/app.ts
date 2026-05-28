import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './app.html', 
  styleUrl: './app.css'      
})
export class App implements OnInit { // <-- A mudança foi apenas nesta linha!
  title = 'O Meu Painel de Investimentos';
  ativos: any[] = [];
  carregando = true;

  // Injetar o HttpClient para fazer chamadas à rede
  private http = inject(HttpClient);

  ngOnInit() {
    this.buscarCotacoes();
  }

  buscarCotacoes() {
    // Chamada à API em Python que está rodando na porta 8000
    this.http.get<any>('http://localhost:8000/api/cotacoes').subscribe({
      next: (resposta) => {
        this.ativos = resposta.ativos;
        this.carregando = false;
      },
      error: (erro) => {
        console.error('Falha ao contactar a API Python:', erro);
        this.carregando = false;
      }
    });
  }
}