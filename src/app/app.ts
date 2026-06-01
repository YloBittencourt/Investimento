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
  // --- NAVEGAÇÃO SPA ---
  visaoAtual: 'home' | 'carteira' = 'home';

  // --- VARIÁVEIS DA PÁGINA INICIAL (BUSCA) ---
  buscaTicker: string = '';
  buscandoFii: boolean = false;
  resultadoBusca: any = null;
  erroBusca: string = '';

  // --- VARIÁVEIS DA CARTEIRA ---
  ativos: any[] = [];
  carregandoTabela = true;
  valorAporte: number = 0;
  comprasRebalanceamento: any[] = [];
  sobraRebalanceamento: number = 0;
  carregandoRebalanceamento = false;
  tickerIA: string = '';
  resultadoIA: any = null;
  carregandoIA = false;
  erroIA: string = '';
  resultadoCarteiraIA: any = null;
  carregandoCarteiraIA = false;
  erroCarteiraIA: string = '';

  private http = inject(HttpClient);
  private cdr = inject(ChangeDetectorRef); 

  ngOnInit() {
    this.buscarCotacoes();
  }

  // --- FUNÇÕES DE NAVEGAÇÃO ---
  mudarVisao(visao: 'home' | 'carteira') {
    this.visaoAtual = visao;
    this.cdr.detectChanges();
  }

  // --- FUNÇÕES DA PÁGINA INICIAL ---
  buscarFiiHome() {
    const tickerLimpo = this.buscaTicker.trim();
    if (!tickerLimpo) return;

    this.buscandoFii = true;
    this.resultadoBusca = null;
    this.erroBusca = '';
    this.cdr.detectChanges();

    this.http.get<any>(`http://localhost:8000/api/fii/${tickerLimpo}`).subscribe({
      next: (res) => {
        if (res.sucesso) { this.resultadoBusca = res; } 
        else { this.erroBusca = res.erro; }
        this.buscandoFii = false;
        this.cdr.detectChanges();
      },
      error: () => {
        this.erroBusca = 'Falha na conexão com o servidor.';
        this.buscandoFii = false;
        this.cdr.detectChanges();
      }
    });
  }

  // --- FUNÇÕES DA CARTEIRA (Já existentes) ---
  buscarCotacoes() {
    this.carregandoTabela = true;
    this.http.get<any>('http://localhost:8000/api/cotacoes').subscribe({
      next: (resposta) => {
        this.ativos = resposta.ativos.map((ativo: any) => ({ ...ativo, editando: false }));
        this.carregandoTabela = false;
        this.cdr.detectChanges();
      },
      error: () => {
        this.carregandoTabela = false;
        this.cdr.detectChanges();
      }
    });
  }

  salvarEdicao(ativo: any) {
    const payload = { quantidade: ativo.quantidade, preco_medio: ativo.precoMedio };
    this.http.put(`http://localhost:8000/api/ativos/${ativo.fundo}`, payload).subscribe({
      next: () => { ativo.editando = false; this.cdr.detectChanges(); }
    });
  }

  calcularRebalanceamento() {
    if (this.valorAporte <= 0) return;
    this.carregandoRebalanceamento = true;
    this.comprasRebalanceamento = [];
    this.cdr.detectChanges();

    this.http.post<any>('http://localhost:8000/api/rebalancear', { aporte: this.valorAporte }).subscribe({
      next: (resposta) => {
        this.comprasRebalanceamento = resposta.compras;
        this.sobraRebalanceamento = resposta.sobra;
        this.carregandoRebalanceamento = false;
        this.cdr.detectChanges();
      },
      error: () => {
        this.carregandoRebalanceamento = false;
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
    this.cdr.detectChanges(); 
    this.http.get<any>(`http://localhost:8000/api/previsao/${tickerLimpo}`).subscribe({
      next: (res) => {
        if (res.sucesso) { this.resultadoIA = res; } else { this.erroIA = res.erro; }
        this.carregandoIA = false;
        this.cdr.detectChanges(); 
      },
      error: () => {
        this.erroIA = `Falha HTTP.`;
        this.carregandoIA = false;
        this.cdr.detectChanges();
      }
    });
  }

  preverRendaCarteira() {
    this.carregandoCarteiraIA = true;
    this.resultadoCarteiraIA = null;
    this.erroCarteiraIA = '';
    this.cdr.detectChanges();
    this.http.get<any>('http://localhost:8000/api/previsao_carteira').subscribe({
      next: (res) => {
        if (res.sucesso) { this.resultadoCarteiraIA = res; } else { this.erroCarteiraIA = res.erro; }
        this.carregandoCarteiraIA = false;
        this.cdr.detectChanges();
      },
      error: () => {
        this.erroCarteiraIA = 'Falha ao conectar com o servidor.';
        this.carregandoCarteiraIA = false;
        this.cdr.detectChanges();
      }
    });
  }
}