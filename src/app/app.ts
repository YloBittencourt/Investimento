import { Component, OnInit, inject, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App implements OnInit {
  ativos: any[] = [];
  carregandoTabela = true;
  
  tickerIA: string = '';
  resultadoIA: any = null;
  carregandoIA = false;
  erroIA: string = '';

  private http = inject(HttpClient);
  // O Desfibrilador do Angular
  private cdr = inject(ChangeDetectorRef); 

  ngOnInit() {
    this.buscarCotacoes();
  }

  buscarCotacoes() {
    this.carregandoTabela = true;
    this.http.get<any>('http://localhost:8000/api/cotacoes').subscribe({
      next: (resposta) => {
        this.ativos = resposta.ativos;
        this.carregandoTabela = false;
        this.cdr.detectChanges(); // Força a tabela a aparecer
      },
      error: (erro) => {
        console.error('Falha na Tabela:', erro);
        this.carregandoTabela = false;
        this.cdr.detectChanges();
      }
    });
  }

  rodarInteligenciaArtificial() {
    const tickerLimpo = this.tickerIA.trim();
    if (!tickerLimpo) return;
    
    this.carregandoIA = true;
    this.resultadoIA = null;
    this.erroIA = '';
    this.cdr.detectChanges(); // Força o "Aguarde..." a aparecer na hora

    this.http.get<any>(`http://localhost:8000/api/previsao/${tickerLimpo}`).subscribe({
      next: (resposta) => {
        if (resposta.sucesso) {
          this.resultadoIA = resposta;
        } else {
          this.erroIA = resposta.erro || 'Erro ao processar modelo.';
        }
        this.carregandoIA = false;
        this.cdr.detectChanges(); // Força o resultado da IA a piscar na tela instantaneamente!
      },
      error: (erro) => {
        console.error('Erro no Oráculo:', erro);
        this.erroIA = `Falha HTTP. Verifique o terminal do Python.`;
        this.carregandoIA = false;
        this.cdr.detectChanges();
      }
    });
  }
}