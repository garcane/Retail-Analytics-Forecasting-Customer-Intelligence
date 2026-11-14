// Every page module registers itself on import. To add a page: create pages/<name>.js that calls registerPage(...)
// (see core/registry.js for the contract) and import it here. Order in the navigation comes from `order`.
import "./overview.js";
import "./sales.js";
import "./delivery.js";
import "./models.js";
import "./risk.js";
import "./forecast.js";
import "./lineage.js";
